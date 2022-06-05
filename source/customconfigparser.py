import configparser


def empty_values_check(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not result:
            raise KeyError('Problem when reading config file. Some values are empty')
        else:
            return result
    return wrapper


class CustomConfigParser(configparser.ConfigParser):
    @empty_values_check
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)