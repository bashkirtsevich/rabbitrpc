# coding=utf-8

RABBITMQ_CONFIG = {
    'queue_name': 'rabbitrpc',
    'exchange': '',
    'reply_timeout': 5, # Floats are ok

    'connection_settings': {
        'host': 'localhost',
        'port': 5672,
        'virtual_host': '/',
        'username': 'guest',
        'password': 'guest',
    }
}