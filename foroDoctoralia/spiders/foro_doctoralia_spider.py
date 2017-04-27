# -*- coding: utf-8 -*-
import urlparse

import scrapy
import sys
from urllib2 import quote

from urllib2 import quote
from foroDoctoralia.items import ForodoctoraliaItem


class foroDoctoraliaSpider(scrapy.Spider):
    name = "doctoralia"
    allowed_domains = ["doctoralia.es"]
    custom_settings = {"SCHEDULER_DISK_QUEUE": 'scrapy.squeues.PickleFifoDiskQueue',
                       "SCHEDULER_MEMORY_QUEUE": 'scrapy.squeues.FifoMemoryQueue'}

    # constructor
    def __init__(self, *a, **kw):
        super(foroDoctoraliaSpider, self).__init__(*a, **kw)
        reload(sys)
        sys.setdefaultencoding("utf-8")

    # método que inicializa la url principal y la manda al método parse
    def start_requests(self):
        urls = 'http://www.doctoralia.es/pregunta-al-experto'
        yield scrapy.Request(url=urls, callback=self.parse)

    # recibo la url de temas y empiezo el crawl
    def parse(self, response):
        # creo un xpath que recorre todos los titulos , textos  y url de cada tema
        items = response.xpath('//section[@class="box askan-themes"]/ol/li')
        for article in items:
            forum_url = article.xpath('.//a/@href').extract_first()
            forum_title = article.xpath('.//a/text()').extract_first()
            # este paso se hace puesto que la url no nos devuelve la url completa y debemos hacer un join con el response url
            forum_url = urlparse.urljoin(response.url, article.xpath('.//a/@href').extract_first())
            # creo un meta para ir insertando nuestros datos
            meta = {'forum_url': forum_url,
                    'forum_title': forum_title
                    }

            yield scrapy.Request(forum_url, callback=self.parse_urlsQuestions, meta=meta)

    def parse_urlsQuestions(self, response):
        # recibo  el meta
        meta = response.meta
        urlQuestion = urlparse.urljoin(response.url,
                                       response.xpath('//p[@class="goto no-icon"]/a/@href').extract_first())
        yield scrapy.Request(urlQuestion, callback=self.parse_questions, meta=meta)

    # método que lee cada url del método parse y la recorre para extraer subject_title y  subject_user(se le manda por meta los datos de parse)
    def parse_questions(self, response):
        # recibo  el meta
        meta = response.meta
        post_num_questions = response.xpath('//div[@class="participants"]/p/b/text()').extract_first()
        post_num_answers = response.xpath('//div[@class="answered"]/p/b/text()').extract_first()
        post_num_experts_agreement = response.xpath('//div[@class="acknowledged"]/p/b/text()').extract_first()
        post_num_patients_grateful = response.xpath('//div[@class="grateful"]/p/b/text()').extract_first()
        meta['post_num_questions'] = post_num_questions
        meta['post_num_answers'] = post_num_answers
        meta['post_num_experts_agreement'] = post_num_experts_agreement
        meta['post_num_patients_grateful'] = post_num_patients_grateful

        userQuest = response.xpath("//div[@class='question']")
        for item in userQuest:
            answers_url = item.xpath(".//following-sibling::p[@class='goto']/a/@href").extract_first()
            #comprobamos si la pregunta tiene más respuestas para mandarle al otro enlace
            if not answers_url == None:
                answers_url = urlparse.urljoin(response.url, answers_url)




            user_question_text = item.xpath(".//following-sibling::a/text()").extract_first().strip()
            # cast de user_question_text a string ,puesto que necesitamos transformarlo a utf-8
            user_question_text = str(user_question_text)
            # transformo el user_question_text a utf8
            user_question_text = unicode(user_question_text, "utf-8")
            user_answer_text = item.xpath(
                ".//following-sibling::div[@class='answer-wrapper']//p[@class='text']/text()").extract_first().strip()
            user_answer_text = str(user_answer_text)
            user_answer_text = unicode(user_answer_text, "utf-8")
            user_answer_name = item.xpath(
                ".//following-sibling::div[@class='answer-wrapper']/div[@class='doctor']/dl/dd/a/text()").extract_first()
            user_answer_specialities = item.xpath(
                ".//following-sibling::div[@class='answer-wrapper']/div[@class='doctor']/dl/dd/p[@class='specialities']/text()").extract_first()
            user_answer_city = item.xpath(
                ".//following-sibling::div[@class='answer-wrapper']/div[@class='doctor']/dl/dd/p[@class='city']/text()").extract_first()
            meta['user_question_text'] = user_question_text
            meta['user_answer_text'] = user_answer_text
            meta['user_answer_name'] = user_answer_name
            meta['user_answer_specialities'] = user_answer_specialities
            meta['user_answer_city'] = user_answer_city
            item = ForodoctoraliaItem()
            item['forum_url'] = meta['forum_url']
            item['forum_title'] = meta['forum_title']
            item['post_num_questions'] = meta['post_num_questions']
            item['post_num_answers'] = meta['post_num_answers']
            item['post_num_experts_agreement'] = meta['post_num_experts_agreement']
            item['post_num_patients_grateful'] = meta['post_num_patients_grateful']
            item['user_question_text'] = meta['user_question_text']
            item['user_answer_text'] = meta['user_answer_text']
            item['user_answer_name'] = meta['user_answer_name']
            item['user_answer_specialities'] = meta['user_answer_specialities']
            item['user_answer_city'] = meta['user_answer_city']
            yield item



