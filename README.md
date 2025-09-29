# TZL


Проект состоит из двух частей:
- **Серверная часть** — поднимается вручную или в Docker.
- **Клиентская часть** — готовый `.exe`, который пользователь просто запускает, вводит логин и работает с сервером.

## 🚀 Запуск сервера

### 1. Клонировать репозиторий
```bash
git clone https://github.com/sta4888/TZL.git
cd TZL
```

### Установить зависимости
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows

pip install -r requirements.txt
```
### Настроить окружение
```shell
cp .env.example .env
```

###  Запустить
```bash
python server.py
```
