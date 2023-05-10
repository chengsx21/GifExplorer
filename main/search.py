from elasticsearch import Elasticsearch

""" ElasticEngine

- search function
    |- perfect search
    |- partial search
- suggest function
    |-

"""


class ElasticSearchEngine():
    # use Kibana to test
    # see http://localhost:5601/app/dev_tools#/console

    # bind to elastic search server
    def __init__(self):
        # self.client = Elasticsearch([{
        #     "host": "127.0.0.1", 
        #     "port": 9200,
        # }])
        self.client = Elasticsearch(
            ['https://router.nasuyun.com:9200'],
            http_auth=('gif_search', '8BOeYq2P3t2JPWn6G6jfVB5top'),
            # scheme="https",
        )

    # [perfect match]
    #   This function is used to search gifs with a particular title
    #   as well as uploader and there's no segmentation for keyword.
    #   Support filters. 
    # [params]
    #   requset: filter info
    #   {
    #       "target": str,
    #       "keyword": str,
    #       "category": str, 
    #       "filter": [
    #           {"range": {"width": {"gte": min, "lte": max}}},
    #           {"range": {"height": {"gte": min, "lte": max}}},
    #           {"range": {"duration": {"gte": min, "lte": max}}}
    #       ],
    #       "tags": [str1, str2, str3 ...]
    #   }
    #   target must be "title" or "uploader"
    # [return value]
    #   list of gif ids, sorted by correlation scores 
    def search_perfect(self, request):

        """ query example
        {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"title.keyword": "still dog"}}, # must
                        {"term": {"category.keyword": "animal"}} # optional
                        {"terms_set": { # optional
                            "tags": {
                                "terms": ["animal", "cat"],
                                "minimum_should_match_script": {
                                    "source": "2"
                                }
                            }
                        }}
                        {"range": {"width": {"gte": 1, "lte": 2}}}, # optional
                        {"range": {"height": {"gte": 1, "lte": 2}}}, # optional
                        {"range": {"duration": {"gte": 1, "lte": 2}}} # optional
                    ]
                }
            }
        }
        """

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
        if target == "uploader":
            must_array.append({"term": {"uploader.keyword": request["keyword"]}})
        else:
            must_array.append({"term": {"title.keyword": request["keyword"]}})
        
        # filter width / height / duration
        must_array += request["filter"]

        # filter category
        must_array.append({"term": {"category.keyword": request["category"]}})

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

        assert must_array
        body["query"]["bool"]["must"] = must_array
        # print(body)
        response = self.client.search(body=body, size=10000)
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]
    
    # [partial match]
    #   This function allows you search gifs with a particular 
    #   title or uploader by proivding partial keywords. Iuput from
    #   user will be segmented and each segment should be included.
    #   Support filters. 
    # [params]
    #   requset: filter info
    #   {
    #       "target": str,
    #       "keyword": str,
    #       "category": str, 
    #       "filter": [
    #           {"range": {"width": {"gte": min, "lte": max}}},
    #           {"range": {"height": {"gte": min, "lte": max}}},
    #           {"range": {"duration": {"gte": min, "lte": max}}}
    #       ],
    #       "tags": [str1, str2, str3 ...]
    #   }
    #   target must be "title" or "uploader"
    # [return value]
    #   list of gif ids, sorted by correlation scores 
    def search_partial(self, request):

        """ query example
        {
            "query": {
                "bool": {
                    "must": [
                        {"match": { # must
                            "title": {
                                "query": "still dog",
                                "operator": "or"
                            }
                        }},
                        {"term": {"category.keyword": "animal"}} # optional
                        {"terms_set": { # optional
                            "tags": {
                                "terms": ["animal", "cat"],
                                "minimum_should_match_script": {
                                    "source": "2"
                                }
                            }
                        }}
                        {"range": {"width": {"gte": 1, "lte": 2}}}, # optional
                        {"range": {"height": {"gte": 1, "lte": 2}}}, # optional
                        {"range": {"duration": {"gte": 1, "lte": 2}}} # optional
                    ]
                }
            }
        }
        """

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
        if target == "uploader":
            must_array.append({
                "match": {
                    "uploader": {
                        "query": request["keyword"],
                        "operator": "or"
                    }
                }
            })
        else:
            must_array.append({
                "match": {
                    "title": {
                        "query": request["keyword"],
                        "operator": "or"
                    }
                }
            })
        
        # filter width / height / duration
        must_array += request["filter"]

        # filter category
        must_array.append({"term": {"category.keyword": request["category"]}})

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

        assert must_array
        body["query"]["bool"]["must"] = must_array
        # print(body)
        response = self.client.search(body=body, size=10000)
        # hits_num = response["hits"]["total"]["value"]
        return [hit["_id"] for hit in response["hits"]["hits"]]

    # [related match]

    # def search_related(self, keyword, target):

    #     if target == "title":
    #         body = {
    #             "query": {
    #                 "match": {
    #                     "title": {
    #                         "query": keyword,
    #                         "operator": "or"
    #                     }
    #                 }
    #             }
    #         }

    # [fuzzy match]
    # params
    #   keyword(str): segmentation for keyword and
    #   segmented words must be adjacent
    # return gif containing keyword as a phrase
    # def search_fuzzy(self, keyword, target):

    #     if target == "title":
    #         body = {
    #             "query": {
    #                 "fuzzy": {
    #                     "title": keyword
    #                 }
    #             }
    #         }
    #     elif target == "uploader":
    #         body = {
    #             "query": {
    #                 "fuzzy": {
    #                     "uploader": keyword
    #                 }
    #             }
    #         }
    #     elif target == "category":
    #         body = {
    #             "query": {
    #                 "fuzzy": {
    #                     "category": keyword
    #                 }
    #             }
    #         }
    #     else:
    #         assert False
    #     response = self.client.search(body=body, size=1000)
    #     # hits_num = response["hits"]["total"]["value"]
    #     return [hit["_id"] for hit in response["hits"]["hits"]]

    # [filter]
    # params
    #   filter(dic): range of width / height / duration
    #   e.g. {
    #       ""
    #       "width": {"min": 1, "max": 10},
    #       "height": {"min": 1, "max": 10},
    #       "duration": {"min": 1, "max": 114514}
    #   }
    # return gif satisfying requirements

    
    # [suggest]
    #   This function supports Auto Completion. We assume that
    #   users confirm input being valid because suggestion &
    #   corrector have been provided before. In other word, 
    #   user_input must be the prefix of suggestions.
    # [params]
    #   user_input(str): type in
    # [return value]
    def suggest_search(self, user_input):

        """
        {
            "suggest": {
                "title_suggest": {
                    "prefix": str,
                    "completion": {
                        "filed": "title"
                    }
                }
            }
        }
        """
        
        body = {
            "suggest": {
                "title_suggest": {
                    "prefix": user_input,
                    "completion": {
                        "field": "suggest"
                    }
                }
            }
        }

        response = self.client.search(body=body)
        return [
            op["_source"]["suggest"] 
            for op in response["suggest"]["title_suggest"][0]["options"]
        ]

if __name__ == "__main__":
    es = ElasticSearchEngine()

    # test perfect match
    request = {
        "target": "title",
        "keyword": "cat picture",
        "category": "cat",
        "filter": [
            {"range": {"width": {"gte": 0, "lte": 100}}},
            {"range": {"height": {"gte": 0, "lte": 100}}},
            {"range": {"duration": {"gte": 0, "lte": 100}}}
        ],
        "tags": ["animal", "cat"]
    }
    print(es.search_perfect(request))

    # test pratial match
    request = {
        "target": "uploader",
        "keyword": "point eight",
        "category": "cat",
        "filter": [
            {"range": {"width": {"gte": 0, "lte": 100}}},
            {"range": {"height": {"gte": 0, "lte": 100}}},
            {"range": {"duration": {"gte": 0, "lte": 100}}}
        ],
        "tags": ["animal", "cat"]
    }
    print(es.search_partial(request))

    # test suggest
    print(es.suggest_search("dog"))

    # # test fuzzy match
    # print(es.search_fuzzy("a large cat", "title"))
    # print(es.search_fuzzy("point eight", "uploader"))
