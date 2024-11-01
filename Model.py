class Model:
    def is_saved(user_id, model_name) -> bool:
        return True  #запрос к бд
    
    
    def is_upload(file) -> bool: #может прилететь что угодно тип Message
        return True  #тут будем проверять файл
    
    def is_done(file, model_name, model_description) -> bool:
        return True  #тут будем вносить модель в базу