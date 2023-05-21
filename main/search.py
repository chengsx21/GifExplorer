"""
Filename: main.py
Author: lutianyu
Contact: luty21@mails.tsinghua.edu.cn
"""
# import synonyms
# import pycorrector
import re
import json
from elasticsearch import Elasticsearch


class ElasticSearchEngine():

    """
    [ElasticEngine]
        functions are named as <target>_search_<search mode>
        e.g. target = suggest/hotwords/personlization
        e.g. search mode = perfect/partial

    - search function
        |- search_perfect
        |- search_partial
        |- search_related
        |- search_fuzzy
    - suggest function
        |- suggest_search
        |- personlization_search
        |- hotwords_search
        |- correct_search
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
        if search_text != "":
            self.client.index(
                index="message_index", body={"message": search_text}
            )
        response = self.client.search(index="gif", body=body, size=10000, preference="primary")
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
        #                 {"term": {"category.keyword": "animal"}}, # optional
        #                 {"terms_set": {
        #                     "tags": {
        #                         "terms": ["animal", "cat"],
        #                         "minimum_should_match_script": {
        #                             "source": "2"
        #                         }
        #                     }
        #                 }},
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
        if search_text != "":
            self.client.index(
                index="message_index", body={"message": search_text}
            )
        response = self.client.search(index="gif", body=body, size=10000, preference="primary")
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]
    
    def search_related(self, request):
        """
        [related search]
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
        #                 {"match": {
        #                    "title": {
        #                       "query": "done",
        #                        "analyzer": "my_analyzer"
        #                     }
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
        if target == "uploader":
            must_array.append({
                "match": {
                    "uploader": {
                        "query": request["keyword"],
                        "analyzer": "my_analyzer"
                    }
                }
            })
        elif target == "title":
            must_array.append({
                "match": {
                    "title": {
                        "query": request["keyword"],
                        "analyzer": "my_analyzer"
                    }
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
        if search_text != "":
            self.client.index(
                index="message_index", body={"message": search_text}
            )
        response = self.client.search(index="gif", body=body, size=10000, preference="primary")
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
        search_text = request["keyword"]
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
                        "query": search_text,
                        "fuzziness": "AUTO",
                        "operator": "and"
                    }
                }
            })
        elif request["target"] == "title":
            must_array.append({
                "match": {
                    "title": {
                        "query": search_text,
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
        if search_text != "":
            self.client.index(
                index="message_index", body={"message": search_text}
            )
        response = self.client.search(index="gif", body=body, size=10000, preference="primary")
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
            "size": 0,
            "aggs": {
                "messages": {
                    "terms": {
                        "size": 10,
                        "field": "message"
                    }
                }
            }
        }
        response = self.client.search(index="message_index", body=body)
        return [
            bucket["key"]
            for bucket in response["aggregations"]["messages"]["buckets"]
        ]

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

        response = self.client.search(index="gif", body=body, size=10000, preference="primary")
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

        response = self.client.search(index="gif", body=body, preference="primary")
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

    def correct_search(self, input, target):
        """
        [correct user input]
            This function will correct user input by providing
            suggestions. Support spelling correction and content
            correction to some extent.

        [params]
            input(str): input from user
            target(str): title(default) or uploader

        [return value]
            list of suggestion string  
        """

        body = {
            "suggest": {
                "correct": {
                }
            }
        }

        phrase = {"field": target}
        body["suggest"]["correct"]["phrase"] = phrase
        body["suggest"]["correct"]["text"] = input

        response = self.client.search(index="gif", body=body, preference="primary")
        return [
            option["text"]
            for option in response["suggest"]["correct"][0]["options"]
        ]


# end ElasticSearchEngine


def test_search_perfect():
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

def test_search_related():
    """
    Unit test for related search
    """

    request1 = {
        "target": "title",
        "keyword": "kid",
        "category": "",
        "filter": [],
        "tags": []
    }

    response = ElasticSearchEngine().search_related(request1)
    assert len(response) >= 0
    # print("response: ", response)
    print("[test related search pass]")

def test_search_fuzzy():
    """
    Unit test for fuzzy search
    """

    request1 = {
        "target": "title",
        "keyword": "dinner,food,delicious",
        "category": "food",
        "filter": [],
        "tags": ["food"]
    }

    response = ElasticSearchEngine().search_fuzzy(request1)
    # print(response)
    assert len(response) >= 0
    print("[test fuzzy search pass]")


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
    response = ElasticSearchEngine().personalization_search({
        "dog": 0.9, "animal": 0.1})
    # print("response: ", response)
    print("[test personlization search pass]")

def test_correct_search():
    """
    Unit test for correct
    """
    response = ElasticSearchEngine().correct_search(
        input="fodd and driink", target="title"
    )
    print("response: ", response)
    print("[correct pass]")


if __name__ == "__main__":

    test_search_perfect()
    test_search_related()
    test_search_fuzzy()
    test_post_metadata()
    test_suggest_search()
    test_personlization_search()
    test_hotwords_search()
    test_correct_search()

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
