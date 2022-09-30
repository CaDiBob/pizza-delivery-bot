flow_properties = {'name': 'Pizzeria', 'slug': 'pizzeria', 'description': 'Адреса и координаты пицерий'}


fields_for_flow = [
    {'type': 'field', 'name': 'Address', 'slug': 'address', 'description': 'address', 'field_type': 'string'},
    {'type': 'field','name': 'Alias', 'slug': 'alias', 'description': 'alias', 'field_type': 'string'},
    {'type': 'field', 'name': 'Longitude', 'slug': 'lon', 'description': 'longitude', 'field_type': 'float'},
    {'type': 'field','name': 'Latitude', 'slug': 'lat', 'description': 'latitude', 'field_type': 'float'},
]

tg_id_field = {
    'type': 'field',
    'name': 'Deliverer_tg_id',
    'slug': 'deliverer_tg_id',
    'deliverer_tg_id': 'lat',
    'description': 'Deliverer telegram id',
    'field_type': 'integer'
}

user_flow_properties = {'name': 'Customer Address', 'slug': 'customers', 'description': 'Адреса и координаты пользователей'}


fields_for_user_flow = [
    {'type': 'field', 'name': 'User ID', 'slug': 'user_id', 'description': 'telegram user id', 'field_type': 'string'},
    {'type': 'field', 'name': 'Longitude', 'slug': 'lon', 'description': 'longitude', 'field_type': 'float'},
    {'type': 'field','name': 'Latitude', 'slug': 'lat', 'description': 'latitude', 'field_type': 'float'},
]
