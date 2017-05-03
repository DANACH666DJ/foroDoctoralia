# -*- coding: utf-8 -*-
import urlparse

import scrapy
import sys

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
        yield scrapy.Request(url=urls, callback=self.parse_one_url)

    # para coger la url de un medicamento
    def parse_one_url(self, response):
        url_one = response.xpath('//section[@class="box askan-themes"]/ol/li/a/@href').extract_first()
        url = urlparse.urljoin(response.url, url_one)
        yield scrapy.Request(url, callback=self.parse_url_medic)

    # para coger la url de medicamentos
    def parse_url_medic(self, response):
        url_medic = response.xpath(
            '//div[@class="container fixed"]/ul[@class="breadcrumb"]/li[2]/a/@href').extract_first()
        url = urlparse.urljoin(response.url, url_medic)
        yield scrapy.Request(url, callback=self.parse_url_list_alphabetic)

    # para coger todos los medicamentos de la letra A a la Z
    def parse_url_list_alphabetic(self, response):
        urls_alphabetic = response.xpath('//nav[@class="abc"]/a')
        for article in urls_alphabetic:
            url = urlparse.urljoin(response.url, article.xpath('.//@href').extract_first())
            #para probar sólo con una letra
            if url == "http://www.doctoralia.es/medicamentos/a":
                yield scrapy.Request(url, callback=self.parse)

    # recibo la url de cada letra y empiezo el crawl
    def parse(self, response):
        # creo un xpath que recorre todos los titulos , textos  y url de cada tema
        items = response.xpath('//div[@class="filter-full"]/div[@id="resultados"]/ul/li')
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
            '''
            # para probar solo con una url de un tema
            if forum_url == "http://www.doctoralia.es/medicamento/abbottselsun-3737":
                yield scrapy.Request(forum_url, callback=self.parse_urlsQuestions, meta=meta)
            '''
        # paginación de la página de alphabetic
        next_page = response.xpath(
            '//div[@class="paging"]//li[@class="active"]/following-sibling::li/a/@href').extract_first()
        next_page = urlparse.urljoin(response.url, next_page)
        if not next_page is None:
            yield scrapy.Request(next_page, callback=self.parse, meta=response.meta)

    def parse_urlsQuestions(self, response):
        # recibo  el meta
        meta = response.meta
        urlQuestion = urlparse.urljoin(response.url,
                                       response.xpath('//p[@class="goto no-icon"]/a/@href').extract_first())
        if not urlQuestion == None:
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
            user_question_text = item.xpath(".//following-sibling::a/text()").extract_first().strip()
            # cast de user_question_text a string ,puesto que necesitamos transformarlo a utf-8
            user_question_text = str(user_question_text)
            # transformo el user_question_text a utf8
            user_question_text = unicode(user_question_text, "utf-8")
            meta['user_question_text'] = user_question_text
            answers_url = item.xpath(".//following-sibling::p[@class='goto']/a/@href").extract_first()
            # comprobamos si la pregunta tiene más respuestas para mandarle al otro enlace y que recoga los datos
            if not answers_url == None:
                answers_url = urlparse.urljoin(response.url, answers_url)
                yield scrapy.Request(answers_url, callback=self.parse_data_answers, meta=meta)
            # si no tiene url de más respuestas sacamos los datos de la principal
            if answers_url == None:
                user_answer_text = item.xpath(
                    ".//following-sibling::div[@class='answer-wrapper']//p[@class='text']/text()").extract_first().strip()
                user_answer_text = str(user_answer_text)
                # transformo el user_answer_text a utf8
                user_answer_text = unicode(user_answer_text, "utf-8")
                user_answer_name = item.xpath(
                    ".//following-sibling::div[@class='answer-wrapper']/div[@class='doctor']/dl/dd/a/text()").extract_first()
                user_answer_specialities = item.xpath(
                    ".//following-sibling::div[@class='answer-wrapper']/div[@class='doctor']/dl/dd/p[@class='specialities']/text()").extract_first()
                user_answer_city = item.xpath(
                    ".//following-sibling::div[@class='answer-wrapper']/div[@class='doctor']/dl/dd/p[@class='city']/text()").extract_first()
                user_answer_url = item.xpath(
                    ".//following-sibling::div[@class='answer-wrapper']/div[@class='doctor']/dl/dd/a/@href").extract_first()
                user_answer_url = urlparse.urljoin(response.url, user_answer_url)
                # print "URLLLLLLLLL***********////////222", user_answer_url
                meta['user_answer_text'] = user_answer_text
                meta['user_answer_name'] = user_answer_name
                meta['user_answer_specialities'] = user_answer_specialities
                meta['user_answer_city'] = user_answer_city
                meta['user_answer_url'] = user_answer_url
                # hacemos otra request con la url del user y le mandamos todos los datos guardados del item
                if user_answer_url is not None:
                    yield scrapy.Request(user_answer_url, callback=self.parse_urlUser, meta=meta, dont_filter=True)
                else:
                    # si el user no tiene url(es decir no tiene datos),ponemos a null todos y creamos el item ya
                    meta['user_answer_num_college'] = None
                    yield self.create_item(meta)

        # paginación de la página de data_answers
        next_page = response.xpath("//li[@class='paginatorNext']/a/@href").extract_first()
        next_page = urlparse.urljoin(response.url, next_page)
        if not next_page is None:
            yield scrapy.Request(next_page, callback=self.parse_questions, meta=response.meta)

    def parse_data_answers(self, response):
        meta = response.meta
        userQuest = response.xpath("//div[@class='answer-wrapper']")
        for item in userQuest:
            user_answer_text = item.xpath(".//p[@class='text']//text()").extract()
            user_answer_text = self.clean_and_flatten(user_answer_text)
            # cast de user_answer_text a string ,puesto que necesitamos transformarlo a utf-8
            user_answer_text = str(user_answer_text)
            # transformo el user_answer_text a utf8
            user_answer_text = unicode(user_answer_text, "utf-8")
            user_answer_name = item.xpath(".//div[@class='doctor']/dl/dd/h3/a/text()").extract_first()
            user_answer_specialities = item.xpath(
                ".//div[@class='doctor']/dl/dd/p[@class='specialities']/text()").extract_first()
            user_answer_city = item.xpath(
                ".//div[@class='doctor']/dl/dd/p[@class='city']/text()").extract_first()
            user_answer_url = item.xpath(".//div[@class='doctor']/dl/dd/h3/a/@href").extract_first()
            user_answer_url = urlparse.urljoin(response.url, user_answer_url)
            meta['user_answer_text'] = user_answer_text
            meta['user_answer_name'] = user_answer_name
            meta['user_answer_specialities'] = user_answer_specialities
            meta['user_answer_city'] = user_answer_city
            meta['user_answer_url'] = user_answer_url
            # hacemos otra request con la url del user y le mandamos todos los datos guardados del item
            if user_answer_url is not None:
                yield scrapy.Request(user_answer_url, callback=self.parse_urlUser, meta=meta, dont_filter=True)
            else:
                # si el user no tiene url(es decir no tiene datos),ponemos a null todos y creamos el item ya
                meta['user_answer_num_college'] = None
                yield self.create_item(meta)

    def parse_urlUser(self, response):
        # recibo los datos
        meta = response.meta
        # los inicio a null por si el usuario no tiene los datos
        meta['user_answer_num_college'] = None

        user_answer_num_college = response.xpath(
            "//div[@class='header-content']/p[@class='regnum']/text()").extract_first()
        meta['user_answer_num_college'] = user_answer_num_college
        yield self.create_item(meta)

    # método para eliminar los espacios en blanco de los textos
    def clean_and_flatten(self, text_list):
        clean_text = []
        for text_str in text_list:
            if text_str == None:
                continue
            if len(text_str.strip()) > 0:
                clean_text.append(text_str.strip())

        return "\n".join(clean_text).strip()

    # método para armar el item con los datos que hemos ido añadiendo al meta
    def create_item(self, meta):
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
        item['user_answer_url'] = meta['user_answer_url']
        item['user_answer_num_college'] = meta['user_answer_num_college']
        return item
