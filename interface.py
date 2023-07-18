# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from datetime import datetime
from config import comunity_token, acces_token
from core import VkTools
from data_store import check_user, add_user, engine
# отправка сообщений


class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.keys = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

    def get_account(self, worksheets, event):
        while True:
            if worksheets:
                worksheet = worksheets.pop()

                'проверка анкеты в бд в соотвествии с event.user_id'
                if not check_user(engine, event.user_id, worksheet['id']):
                    'добавление анкеты в бд в соотвествии с event.user_id'
                    add_user(engine, event.user_id, worksheet['id'])

                    yield worksheet
            else:
                worksheets = self.vk_tools.search_worksheet(
                    self.params, self.offset)

# обработка событий / получение сообщений
    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет друг, {self.params["name"]}')

                    self.keys = self.params.keys()
                    for i in self.keys:
                        if self.params[i] is None:
                            if self.params['name'] is None:
                                self.message_send(event.user_id, 'Введите ваше имя и фамилию:')
                                for k in self.longpoll.listen():
                                    if k.type == VkEventType.MESSAGE_NEW and k.to_me:
                                        self.params['name'] = k.text
                                        break

                            elif self.params['sex'] is None:
                                self.message_send(event.user_id, 'Введите свой пол (1-м, 2-ж):')
                                for k in self.longpoll.listen():
                                    if k.type == VkEventType.MESSAGE_NEW and k.to_me:
                                        self.params['sex'] = int(k.text)
                                        break

                            elif self.params['city'] is None:
                                self.message_send(event.user_id, 'Введите город:')
                                for k in self.longpoll.listen():
                                    if k.type == VkEventType.MESSAGE_NEW and k.to_me:
                                        self.params['city'] = k.text
                                        break

                            elif self.params['year'] is None:
                                self.message_send(event.user_id, 'Введите дату рождения (дд.мм.гггг):')
                                for k in self.longpoll.listen():
                                    if k.type == VkEventType.MESSAGE_NEW and k.to_me:
                                        self.params['year'] = datetime.now().year - int(k.text.split('.')[2])
                                        break

                    self.message_send(event.user_id, 'Вы успешно зарегистрировались!')

                elif event.text.lower() == 'поиск':
                    '''Логика для поиска анкет'''
                    self.message_send(
                        event.user_id, 'Начинаем поиск')
                    a = next(iter(self.get_account(self.worksheets, event)))
                    if a:
                        photos = self.vk_tools.get_photos(a['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 10

                        self.message_send(
                            event.user_id,
                            f'имя: {a["name"]} ссылка: vk.com/id{a["id"]}',
                            attachment=photo_string
                        )

                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'До новых встреч')
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()
