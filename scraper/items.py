import scrapy

class StoreItem(scrapy.Item):
    province= scrapy.Field()
    city= scrapy.Field()
    country= scrapy.Field()
    town= scrapy.Field()
    street= scrapy.Field()
    road= scrapy.Field()
    type= scrapy.Field()
    estate_name_zh= scrapy.Field()
    flat= scrapy.Field()
    building_name_zh= scrapy.Field()
    floor= scrapy.Field()
    unit= scrapy.Field()
    area= scrapy.Field()
    house_type= scrapy.Field()
    deal_date= scrapy.Field()
    deal_price= scrapy.Field()
    developer= scrapy.Field()
    pass
