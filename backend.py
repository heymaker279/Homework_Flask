from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask.views import MethodView
from dotenv import dotenv_values

env = dotenv_values(".env")
app = Flask("backend")
app.config['JSON_AS_ASCII'] = False
engine = create_engine(
    f'postgresql://{env["DB_USER"]}:{env["DB_PASSWORD"]}@{env["DB_HOST"]}:{env["DB_PORT"]}/{env["DB_NAME"]}')
Base = declarative_base()
Session = sessionmaker(bind=engine)


class HttpError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def http_error_handler(er: HttpError):
    response = jsonify({'status': 'error', 'message': er.message})
    response.status_code = er.status_code
    return response


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(60), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(100))


class Advertisement(Base):
    __tablename__ = 'advertisements'
    id = Column(Integer, primary_key=True)
    header = Column(String(64), nullable=False)
    description = Column(String, nullable=False)
    registration_time = Column(DateTime, server_default=func.now())
    owner = Column(ForeignKey(User.id))


Base.metadata.create_all(engine)


def get_item(session, item_id, cls):
    response = session.query(cls).get(item_id)
    if response is None:
        raise HttpError(404, f'{cls.__name__} does not exist')
    return response


class AdvView(MethodView):

    def get(self, adv_id):
        with Session() as session:
            adv = get_item(session, adv_id, Advertisement)
            return jsonify({
                'header': adv.header,
                'registration_time': adv.registration_time.isoformat(),
                'description': adv.description,
                'owner': adv.owner
            })

    def post(self):
        adv_data = request.json
        with Session() as session:
            new_adv = Advertisement(header=adv_data['header'], description=adv_data['description'],
                                    owner=adv_data['owner'])
            session.add(new_adv)
            session.commit()
            return jsonify({'status': 'ok', 'id': new_adv.id})

    def patch(self, adv_id):
        adv_data = request.json
        with Session() as session:
            adv = get_item(session, adv_id, Advertisement)
            for key, value in adv_data.items():
                setattr(adv, key, value)
            session.commit()
        return jsonify({'status': 'ok'})

    def delete(self, adv_id):
        with Session() as session:
            adv = get_item(session, adv_id, Advertisement)
            session.delete(adv)
            session.commit()
        return jsonify({'status': 'Ok'})


class UserView(MethodView):

    def get(self, user_id):
        with Session() as session:
            user = get_item(session, user_id, User)
            return jsonify({
                'name': user.name,
                'email': user.email,
                'password': user.password,
            })

    def post(self):
        user_data = request.json
        with Session() as session:
            new_user = User(name=user_data['name'], email=user_data['email'], password=user_data['password'])
            session.add(new_user)
            session.commit()
            return jsonify({'status': 'ok', 'id': new_user.id})

    def patch(self, user_id):
        user_data = request.json
        with Session() as session:
            user = get_item(session, user_id, User)
            for key, value in user_data.items():
                setattr(user, key, value)
            session.commit()
        return jsonify({'status': 'ok'})

    def delete(self, user_id):
        with Session() as session:
            user = get_item(session, user_id, User)
            session.delete(user)
            session.commit()
        return jsonify({'status': 'Ok'})


app.add_url_rule('/adv/<int:adv_id>', view_func=AdvView.as_view('adv_get'), methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/adv', view_func=AdvView.as_view('adv_post'), methods=['POST'])
app.add_url_rule('/user/<int:user_id>', view_func=UserView.as_view('user_get'), methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/user', view_func=UserView.as_view('user_post'), methods=['POST'])
app.run()
