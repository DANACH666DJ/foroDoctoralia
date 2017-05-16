# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ForodoctoraliaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    forum_url = scrapy.Field()
    forum_title = scrapy.Field()
    unique_id_medicament = scrapy.Field()
    post_num_questions = scrapy.Field()
    post_num_answers = scrapy.Field()
    post_num_experts_agreement = scrapy.Field()
    post_num_patients_grateful = scrapy.Field()
    user_question_text = scrapy.Field()
    user_answer_text = scrapy.Field()
    user_answer_name = scrapy.Field()
    user_answer_specialities = scrapy.Field()
    user_answer_city = scrapy.Field()
    user_answer_url = scrapy.Field()
    user_answer_num_college = scrapy.Field()

    pass
