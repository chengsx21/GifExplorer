"""
Filename: main.py
Author: lutianyu
Contact: luty21@mails.tsinghua.edu.cn
"""
import synonyms
import pycorrector
import re
import json
from elasticsearch import Elasticsearch


def contains_chinese(sentence: str):
    """
        Test if sentence has Chinese
    """
    if re.search(".*[\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A].*", sentence):
        return True
    else:
        return False

def get_synonyms(sentence):
    """
    return the synonyms of keywords of 'sentence'
    """
    # 英文情形

    # 中文情形
    keywords_list = synonyms.keywords(sentence, topK=3)  # 从输入文本中提取 3 个关键词
    synonyms_list = []
    for keyword in keywords_list:
        synonyms_list += synonyms.nearby(keyword)[0][:3]  # 每个词语取 3 个近义词
    return synonyms_list


class ElasticSearchEngine():

    """
    [ElasticEngine]
        functions are named as <target>_search_<search mode>
        e.g. target = suggest/hotwords/personlization
        e.g. search mode = perfect/partial

    - search function
        |- search_perfect
        |- search_partial
    - suggest function
        |- suggest_search
        |- personlization_search
        |- hotwords_search
    - synchronization function
        |- post metadata
    - test function
        |- test_search_perfect
        |- test_post_metadata
        |- test_suggest_search
        |- test_personlization_search
        |- test_hotwords_search
    """

    # Use Kibana to test
    # Local test: see http://localhost:5601/app/dev_tools#/console
    # Nasuyun test: see https://kibana.nasuyun.com/app/kibana#/dev_tools/console

    # bind to elastic search server
    def __init__(self):
        # self.client = Elasticsearch([{"host": "127.0.0.1", "port": 9200}])
        self.client = Elasticsearch(
            ['https://router.nasuyun.com:9200'],
            http_auth=('gif_search', '8BOeYq2P3t2JPWn6G6jfVB5top'),
            scheme="https",
        )

    def search_perfect(self, request):
        """
        [perfect match]
            This function is used to search gifs with a particular title
            as well as uploader and there's no segmentation for keyword.
            Support filters.
        [params]
            requset: dic of filter info
            {
                "target": str, "title" or "uploader" (default="")
                "keyword": str, (default="")
                "category": str, (default="")
                "filter": [
                    {"range": {"width": {"gte": min, "lte": max}}},
                    {"range": {"height": {"gte": min, "lte": max}}},
                    {"range": {"duration": {"gte": min, "lte": max}}}
                ], (default=[])
                "tags": [str1, str2, str3 ...] (default=[])
            }
            all segments are optional!
        [return value]
            list of gif ids, sorted by correlation scores
        """

        # query example
        # {
        #     "query": {
        #         "bool": {
        #             "must": [
        #                 {"term": {"title.keyword": "still dog"}},
        #                 {"term": {"category.keyword": "animal"}}
        #                 {"terms_set": {
        #                     "tags": {
        #                         "terms": ["animal", "cat"],
        #                         "minimum_should_match_script": {
        #                             "source": "2"
        #                         }
        #                     }
        #                 }}
        #                 {"range": {"width": {"gte": 1, "lte": 2}}},
        #                 {"range": {"height": {"gte": 1, "lte": 2}}},
        #                 {"range": {"duration": {"gte": 1, "lte": 2}}}
        #             ]
        #         }
        #     }
        # }

        body = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }

        # match title or uploader
        must_array = []
        target = request["target"]
        search_text = request["keyword"]
        if target == "uploader":
            must_array.append(
                {"term": {"uploader.keyword": search_text}})
        elif target == "title":
            must_array.append({"term": {"title.keyword": search_text}})

        # filter width / height / duration
        must_array += request["filter"]

        # filter category
        if request["category"] != "":
            must_array.append(
                {"term": {"category.keyword": request["category"]}})

        # filter tags
        # tags provided by user should be the subset of real gif tags
        tags = request["tags"]
        if tags:
            must_array.append({"terms_set": {
                "tags": {
                    "terms": tags,
                    "minimum_should_match_script": {
                        "source": str(len(tags))
                    }
                }
            }})

        body["query"]["bool"]["must"] = must_array
        self.client.index(index="message_index", body={"message": search_text})
        response = self.client.search(body=body, size=10000, preference="primary")
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]

    def search_partial(self, request):
        """
        [partial match]
            This function allows you search gifs with a particular
            title or uploader by proivding partial keywords. Iuput from
            user will be segmented and each segment should be included.
            Support filters.

        [params]
            requset: filter info
            {
                "target": str, (default="")
                "keyword": str, (default="")
                "category": str, (default="")
                "filter": [
                    {"range": {"width": {"gte": min, "lte": max}}},
                    {"range": {"height": {"gte": min, "lte": max}}},
                    {"range": {"duration": {"gte": min, "lte": max}}}
                ], (default=[])
                "tags": [str1, str2, str3 ...] (default=[])
            }
            all segments are optional

        [return value]
            list of gif ids, sorted by correlation scores
        """

        # query example
        # {
        #     "query": {
        #         "bool": {
        #             "must": [
        #                 {"match": {
        #                     "title": {
        #                         "query": "still dog",
        #                         "operator": "and"
        #                     }
        #                 }},
        #                 {"term": {"category.keyword": "animal"}} # optional
        #                 {"terms_set": {
        #                     "tags": {
        #                         "terms": ["animal", "cat"],
        #                         "minimum_should_match_script": {
        #                             "source": "2"
        #                         }
        #                     }
        #                 }}
        #                 {"range": {"width": {"gte": 1, "lte": 2}}},
        #                 {"range": {"height": {"gte": 1, "lte": 2}}},
        #                 {"range": {"duration": {"gte": 1, "lte": 2}}}
        #             ]
        #         }
        #     }
        # }

        body = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }

        # match title or uploader
        must_array = []
        target = request["target"]
        search_text = request["keyword"]
        if target == "uploader":
            must_array.append({
                "match": {
                    "uploader": {
                        "query": request["keyword"],
                        "operator": "and"
                    }
                }
            })
        elif target == "title":
            must_array.append({
                "match": {
                    "title": {
                        "query": request["keyword"],
                        "operator": "and"
                    }
                }
            })

        # filter width / height / duration
        must_array += request["filter"]

        # filter category
        if request["category"] != "":
            must_array.append({
                "term": {
                    "category.keyword": request["category"]
                }
            })


        # filter tags
        # tags provided by user should be the subset of real gif tags
        tags = request["tags"]
        if tags:
            must_array.append({
                "terms_set": {
                    "tags": {
                        "terms": tags,
                        "minimum_should_match_script": {
                            "source": str(len(tags))
                        }
                    }
                }
            })

        body["query"]["bool"]["must"] = must_array
        self.client.index(index="message_index", body={"message": search_text})
        response = self.client.search(body=body, size=10000, preference="primary")
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]

    def search_related(self, request):
        """
        [related match]
            This function search targets based on relevant words.

        [params]
            requset: filter info
            {
                "target": str, (default="")
                "keyword": str, (keywords actually, must) 
                "category": str, (default="")
                "filter": [
                    {"range": {"width": {"gte": min, "lte": max}}},
                    {"range": {"height": {"gte": min, "lte": max}}},
                    {"range": {"duration": {"gte": min, "lte": max}}}
                ], (default=[])
                "tags": [str1, str2, str3 ...] (default=[])
            }

        [return value]
            list of gif ids
        """

        # query example
        # {
        #     "query": {
        #         "bool": {
        #             "must": [
        #                 {"terms": {
        #                       "title": ["dinner", "supper"]
        #                   }},
        #                 {"term": {"category.keyword": "animal"}} # optional
        #                 {"terms_set": {
        #                     "tags": {
        #                         "terms": ["animal", "cat"],
        #                         "minimum_should_match_script": {
        #                             "source": "2"
        #                         }
        #                     }
        #                 }}
        #                 {"range": {"width": {"gte": 1, "lte": 2}}},
        #                 {"range": {"height": {"gte": 1, "lte": 2}}},
        #                 {"range": {"duration": {"gte": 1, "lte": 2}}}
        #             ]
        #         }
        #     }
        # }

        body = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }

        # match title or uploader
        must_array = []
        target = request["target"]
        search_text = request["keyword"]
        synonyms_list = get_synonyms(request["keyword"])
        # print(f"synonyms_list = {synonyms_list}")
        if target == "uploader":
            must_array.append({
                "terms": {
                    "uploader": synonyms_list
                }
            })
        elif target == "title":
            must_array.append({
                "terms": {
                    "title": synonyms_list
                }
            })

        # filter width / height / duration
        must_array += request["filter"]

        # filter category
        if request["category"] != "":
            must_array.append(
                {"term": {"category.keyword": request["category"]}})

        # filter tags
        # tags provided by user should be the subset of real gif tags
        tags = request["tags"]
        if tags:
            must_array.append({"terms_set": {
                "tags": {
                    "terms": tags,
                    "minimum_should_match_script": {
                        "source": str(len(tags))
                    }
                }
            }})

        body["query"]["bool"]["must"] = must_array
        self.client.index(index="message_index", body={"message": search_text})
        response = self.client.search(body=body, size=10000, preference="primary")
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]

    def search_fuzzy(self, request):
        '''
        [fuzzy match]
        [params]
            requset: filter info
            {
                "target": str, (default="")
                "keyword": str, (default="")
                "category": str, (default="")
                "filter": [
                    {"range": {"width": {"gte": min, "lte": max}}},
                    {"range": {"height": {"gte": min, "lte": max}}},
                    {"range": {"duration": {"gte": min, "lte": max}}}
                ], (default=[])
                "tags": [str1, str2, str3 ...] (default=[])
            }
            all segments are optional
        [return]
            list of gif ids, sorted by correlation scores
        '''

        body = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }

        # match title or uploader
        must_array = []
        if request["target"] == "uploader":
            # must_array.append({
            #     "fuzzy": {
            #         "title": {
            #             "value": request["keyword"],
            #             "fuzziness": "AUTO",
            #             # "transpositions": True,
            #             # fuzziness：最大编辑距离，一个字符串要与另一个字符串相同必须更改的一个字符数】。默认为AUTO。
            #             # prefix_length：不会被“模糊化”的初始字符数。这有助于减少必须检查的术语数量。默认为0。
            #             # max_expansions：fuzzy查询将扩展到的最大术语数。默认为50。
            #             # transpositions：是否支持模糊转置（ab→ ba）。默认值为false。
            #         }
            #     }
            # })
            must_array.append({
                "match": {
                    "uploader": {
                        "query": request["keyword"],
                        "fuzziness": "AUTO",
                        "operator": "and"
                    }
                }
            })
        elif request["target"] == "title":
            must_array.append({
                "match": {
                    "title": {
                        "query": request["keyword"],
                        "fuzziness": "AUTO",
                        "operator": "and"
                    }
                }
            })

        # filter width / height / duration
        must_array += request["filter"]

        # filter category
        if request["category"] != "":
            must_array.append({
                "term": {
                    "category.keyword": request["category"]
                }
            })

        # filter tags
        # tags provided by user should be the subset of real gif tags
        tags = request["tags"]
        if tags:
            must_array.append({"terms_set": {
                "tags": {
                    "terms": tags,
                    "minimum_should_match_script": {
                        "source": str(len(tags))
                    }
                }
            }})

        body["query"]["bool"]["must"] = must_array
       
        response = self.client.search(body=body, size=10000, preference="primary")

        # from pprint import pprint
        # pprint(response["hits"]["hits"][:10])
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]


    def hotwords_search(self):
        """
        [hot words]
            Provide hot candidate words based on search history.
   
        [params]
            None

        [return value]
            list of hot candidate words
        """

        body = {
            "size" : 0,  
            "aggs" : {   
                "messages" : {   
                    "terms" : {   
                        "size" : 10,
                        "field" : "message"
                    }
                }
            }
        }
        response = self.client.search(index="message_index", body=body)
        return [bucket["key"] for bucket in response["aggregations"]["messages"]["buckets"]]

    def personalization_search(self, tag_fre):
        """
        [personlization]
            This function supports personlization. Given users' browse
            history, elastic search will return most relavent gif ids.

        [params]
            tag_fre(dic): tag frequency table, {"animal": "10", "cute": "2"}

        [return val]
            list of gif id
        """

        # body example
        # {
        #   "query": {
        #     "bool": {
        #       "should": [
        #         {
        #           "term": {
        #             "tags": {
        #             "value": "animal",
        #             "boost": 2.5
        #             }
        #           }
        #         },
        #         {
        #           "term": {
        #             "tags": {
        #             "value": "dog",
        #             "boost": 10
        #             }
        #           }
        #         }
        #       ]
        #     }
        #   }
        # }

        body = {
            "query": {
                "bool": {
                    "should": [
                    ]
                }
            }
        }

        for key, val in tag_fre.items():
            body["query"]["bool"]["should"].append({
                "term": {
                    "tags": {
                        "value": key,
                        "boost": val
                    }
                }
            })

        response = self.client.search(body=body, size=10000)
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]


    def suggest_search(self, user_input):
        """
        [suggest]
            This function supports Auto Completion. We assume that
            users confirm input being valid because suggestion &
            corrector have been provided before. In other word,
            user_input must be the prefix of suggestions.

        [params]
            user_input(str): type in

        [return value]
            list of suggestion string
        """

        # {
        #     "suggest": {
        #         "title_suggest": {
        #             "prefix": str,
        #             "completion": {
        #                 "filed": "title",
        #                 "skip_duplicates": true
        #             }
        #         }
        #     }
        # }

        body = {
            "suggest": {
                "title_suggest": {
                    "prefix": user_input,
                    "completion": {
                        "field": "suggest",
                        "skip_duplicates": True
                    }
                }
            }
        }

        response = self.client.search(body=body, size=10000)
        return [
            op["_source"]["suggest"]
            for op in response["suggest"]["title_suggest"][0]["options"]
        ]

    def post_metadata(self, data):
        """
        [post meta data]
            This function is called when uploading or updating gifs
            to guarantee synchronization between Postgre and ES.

        [params]
            data(dict): necessary metadata for SEARCH
            e.g.
            {
                "id" : 16,
                "title" : "Singing",
                "uploader" : "Chengsx21",
                "width" : 1280,
                "height" : 720,
                "category" : "food",
                "tags" : [
                    "funny",
                    "people",
                    "gathering"
                ],
                "duration" : 5.2,
                "pub_time" : "2023-04-23T15:32:59.514Z",
                "like" : 0,
                "is_liked" : false,
            }

        [return value]
            response of relevant es request
        """

        data["suggestion"] = data["title"]
        response = self.client.index(
            index="gif",
            id=int(data["id"]),
            body=json.dumps(data)
        )
        return response

    def correct(self, input):
        if contains_chinese(input):
            corrected_sent, detail = pycorrector.correct(input)
        else:
            corrected_sent, detail = pycorrector.en_correct(input)
        # print(f"corrected_sent = {corrected_sent}")
        return corrected_sent

# end ElasticSearchEngine


def test_perfect_search():
    """
    Unit test for perfect_metadata
    """

    request1 = {
        "target": "uploader",
        "keyword": "spider",
        "category": "",
        "filter": [],
        "tags": []
    }

    response = ElasticSearchEngine().search_perfect(request1)
    # print(response)
    assert len(response) > 0
    print("[test perfect search pass]")


def test_post_metadata():
    """
    Unit test for post_metadata 
    """

    request1 = {
        "id": 16,
        "title": "Singing",
        "uploader": "Chengsx21",
        "width": 1280,
        "height": 720,
        "category": "food",
        "tags": [
            "funny",
            "people",
            "gathering"
        ],
        "duration": 5.2,
        "pub_time": "2023-04-23T15:32:59.514Z",
        "like": 0,
        "is_liked": False,
    }

    response = ElasticSearchEngine().post_metadata(request1)

    # unit test
    # print("response: ", response)
    assert int(response["_id"]) == request1["id"]
    print("[test post metadata pass]")


def test_hotwords_search():
    """
    Unit test for hot search
    """

    response = ElasticSearchEngine().hotwords_search()
    print("response: ", response)
    assert response
    print("[test hot word pass]")


def test_suggest_search():
    """
    Unit test for suggest search
    """
    response = ElasticSearchEngine().suggest_search("f")
    # print("response: ", response)
    for op in response:
        assert op[0] == "f" or op[0] == "F"
    print("[test suggest search pass]")


def test_personlization_search():
    """
    Unit test for personlization search
    """
    response = ElasticSearchEngine().personalization_search({"dog": 0.9, "animal": 0.1})
    # print("response: ", response)
    print("[test personlization search pass]")


def test_synonyms(sentence):
    synonyms_list = get_synonyms(sentence)
    print(f"synonyms_list = {synonyms_list}")
    print("[test synonyms pass]")


def test_correct(sentence):
    corrected = ElasticSearchEngine().correct(sentence)
    print(f"corrected = {corrected}")
    print("[test correct pass]")


if __name__ == "__main__":

    test_perfect_search()
    test_post_metadata()
    test_suggest_search()
    test_personlization_search()
    test_hotwords_search()
    test_synonyms("fun")   # assert ['fun', 'Fun', 'phone']
    test_synonyms("food")  # assert ['food', 'crops', 'cooked']
    test_synonyms("食物")  # assert ['食物', '食材', '水果']
    test_correct("falut sentence")  # assert 'fault sentence'
    test_correct("少先队员因该为老人让坐")  # assert '少先队员应该为老人让座'


# if __name__ == "__main__":

#     # test perfect match
#     request1 = {
#         "target": "uploader",
#         "filter": [],
#         "category": "",
#         "tags": [],
#         "keyword": "spider126"
#     }
#     print(es.search_perfect(request1))

    # test pratial match
    # request2 = {
    #     "target": "uploader",
    #     "keyword": "point eight",
    #     "category": "cat",
    #     "filter": [
    #         {"range": {"width": {"gte": 0, "lte": 100}}},
    #         {"range": {"height": {"gte": 0, "lte": 100}}},
    #         {"range": {"duration": {"gte": 0, "lte": 100}}}
    #     ],
    #     "tags": ["animal", "cat"]
    # }
    # print(es.search_partial(request2))

    # # test suggest

    # # test fuzzy match
    # print(es.search_fuzzy("a large cat", "title"))
    # print(es.search_fuzzy("point eight", "uploader"))
