import telebot
import json
from dateutil import parser
from dateutil.relativedelta import relativedelta
from config import API_TOKEN

bot = telebot.TeleBot(API_TOKEN)


def aggregate_salary_data(dt_from_str, dt_upto_str, group_type, additional_data):
    # Преобразование строк в объекты datetime
    dt_from = parser.parse(dt_from_str)
    dt_upto = parser.parse(dt_upto_str)

    # Преобразование дат в additional_data в объекты datetime
    additional_data = [{'dt': parser.parse(item['dt']), 'amount': item['value']} for item in additional_data if
                       'dt' in item and 'value' in item]

    # Определение шага агрегации
    if group_type == "hour":
        step = relativedelta(hours=1)
    elif group_type == "day":
        step = relativedelta(days=1)
    elif group_type == "month":
        step = relativedelta(months=1)

    # Инициализация переменных
    dataset = []
    labels = []
    current_dt = dt_from

    # Цикл по временным интервалам
    while current_dt < dt_upto:
        total_salary = 0
        # Используем дополнительные данные, если они доступны
        for data in additional_data:
            if data['dt'] >= current_dt and data['dt'] < current_dt + step:
                total_salary += data['amount']

        # Добавление суммы зарплат в dataset
        dataset.append(total_salary)
        # Добавление метки (дата начала интервала) в labels
        labels.append(current_dt.isoformat())

        # Переход к следующему интервалу
        current_dt += step

    # Добавляем последний элемент в dataset, если dt_upto находится вне диапазона дат в additional_data
    if current_dt == dt_upto:
        dataset.append(0)
        labels.append(current_dt.isoformat())

    return {"dataset": dataset, "labels": labels}


@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f'Привет, {user_name}! Отправь мне JSON с входными данными для агрегации зарплат.')


@bot.message_handler(func=lambda message: True)
def handle_json(message):
    try:
        input_data = json.loads(message.text)
        result = aggregate_salary_data(input_data["dt_from"], input_data["dt_upto"], input_data["group_type"], additional_data)

        # Форматирование строки с метками для вывода на отдельных строках с отступом в 11 пробелов
        labels = result['labels']
        # Первая запись выводится на той же строке, что и "labels"
        first_label = f'"{labels[0]}"'
        # Остальные записи выводятся каждые 4 на новой строке с отступом
        other_labels = ',\n' + ' ' * 11 + ',\n'.join(f'"{label}"' for label in labels[1:])
        # Объединяем первую и остальные записи
        labels_str = first_label + other_labels

        # Форматирование строки с датасетом для вывода в виде сплошного текста
        dataset_str = ', '.join(str(data) for data in result['dataset'])

        # Формируем финальный вывод
        response_text = f'{{\n  "dataset": [{dataset_str}],\n  "labels": [\n{labels_str}\n  ]\n}}'

        bot.send_message(message.chat.id, response_text)
    except json.JSONDecodeError:
        bot.send_message(message.chat.id, "Ошибка: неверный формат JSON. Пожалуйста, отправьте корректные данные.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")


if __name__ == '__main__':
    # Чтение данных из файлов
    with open('sample_collection.metadata.json', 'r') as metadata_file:
        metadata = json.load(metadata_file)

    with open('sample_collection.json', 'r') as json_file:
        additional_data = json.load(json_file)

    # Запуск бота
    bot.polling(none_stop=True)
