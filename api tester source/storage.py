from datetime import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Collection(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    requests = relationship("SavedRequest", back_populates="collection", cascade="all, delete-orphan")

class SavedRequest(Base):
    __tablename__ = 'saved_requests'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    url = Column(String(2048), nullable=False)
    headers = Column(Text)  # JSON string
    body = Column(Text)
    collection_id = Column(Integer, ForeignKey('collections.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    collection = relationship("Collection", back_populates="requests")

class RequestHistory(Base):
    __tablename__ = 'request_history'
    id = Column(Integer, primary_key=True)
    method = Column(String(10), nullable=False)
    url = Column(String(2048), nullable=False)
    headers = Column(Text)  # JSON string
    body = Column(Text)
    response_code = Column(Integer)
    response_body = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Environment(Base):
    __tablename__ = 'environments'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    variables = Column(Text)  # JSON string of key/value pairs
    created_at = Column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    url = Column(String(2048), nullable=False)
    headers = Column(Text)
    body = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Storage:
    def __init__(self, db_path='requests.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_to_history(self, method, url, headers, body, response_code, response_body):
        """Add a request and its response to history."""
        with self.Session() as session:
            history = RequestHistory(
                method=method,
                url=url,
                headers=headers,
                body=body,
                response_code=response_code,
                response_body=response_body
            )
            session.add(history)
            session.commit()
            return history.id

    # Environment methods
    def create_environment(self, name, variables_json="{}"):
        with self.Session() as session:
            env = Environment(name=name, variables=variables_json)
            session.add(env)
            session.commit()
            return env.id

    def get_environments(self):
        with self.Session() as session:
            return session.query(Environment).order_by(Environment.name).all()

    def update_environment(self, env_id, variables_json):
        with self.Session() as session:
            env = session.query(Environment).filter(Environment.id == env_id).first()
            if env:
                env.variables = variables_json
                session.commit()
                return True
            return False
    
    def get_environment(self, env_id):
        with self.Session() as session:
            return session.query(Environment).filter(Environment.id == env_id).first()

    def delete_environment(self, env_id):
        with self.Session() as session:
            env = session.query(Environment).filter(Environment.id == env_id).first()
            if env:
                session.delete(env)
                session.commit()
                return True
            return False

    # Template methods
    def save_template(self, name, method, url, headers=None, body=None):
        with self.Session() as session:
            t = Template(name=name, method=method, url=url, headers=headers, body=body)
            session.add(t)
            session.commit()
            return t.id

    def update_template(self, template_id, name=None, method=None, url=None, headers=None, body=None):
        with self.Session() as session:
            t = session.query(Template).filter(Template.id == template_id).first()
            if not t:
                return False
            if name is not None:
                t.name = name
            if method is not None:
                t.method = method
            if url is not None:
                t.url = url
            if headers is not None:
                t.headers = headers
            if body is not None:
                t.body = body
            session.commit()
            return True

    def get_templates(self):
        with self.Session() as session:
            return session.query(Template).order_by(Template.created_at.desc()).all()

    def get_template(self, template_id):
        with self.Session() as session:
            return session.query(Template).filter(Template.id == template_id).first()

    def delete_template(self, template_id):
        with self.Session() as session:
            t = session.query(Template).filter(Template.id == template_id).first()
            if t:
                session.delete(t)
                session.commit()
                return True
            return False

    # Import / Export helpers
    def export_environments(self):
        """Return JSON string of all environments."""
        with self.Session() as session:
            envs = session.query(Environment).all()
            out = []
            for e in envs:
                out.append({
                    'id': e.id,
                    'name': e.name,
                    'variables': e.variables,
                    'created_at': e.created_at.isoformat() if e.created_at else None,
                })
            return json.dumps(out, indent=2)

    def import_environments(self, json_str):
        """Import environments from a JSON string. Returns count imported."""
        try:
            data = json.loads(json_str)
        except Exception:
            return 0
        count = 0
        with self.Session() as session:
            for item in data:
                name = item.get('name') or 'imported'
                variables = item.get('variables') or '{}'
                env = Environment(name=name, variables=variables)
                session.add(env)
                count += 1
            session.commit()
        return count

    def export_templates(self):
        with self.Session() as session:
            tpls = session.query(Template).all()
            out = []
            for t in tpls:
                out.append({
                    'id': t.id,
                    'name': t.name,
                    'method': t.method,
                    'url': t.url,
                    'headers': t.headers,
                    'body': t.body,
                    'created_at': t.created_at.isoformat() if t.created_at else None,
                })
            return json.dumps(out, indent=2)

    def import_templates(self, json_str):
        try:
            data = json.loads(json_str)
        except Exception:
            return 0
        count = 0
        with self.Session() as session:
            for item in data:
                t = Template(
                    name=item.get('name') or 'imported',
                    method=item.get('method') or 'GET',
                    url=item.get('url') or '',
                    headers=item.get('headers') or None,
                    body=item.get('body') or None,
                )
                session.add(t)
                count += 1
            session.commit()
        return count

    def get_history(self, limit=50):
        """Get recent requests from history."""
        with self.Session() as session:
            return session.query(RequestHistory)\
                .order_by(RequestHistory.created_at.desc())\
                .limit(limit)\
                .all()

    def create_collection(self, name):
        """Create a new request collection."""
        with self.Session() as session:
            collection = Collection(name=name)
            session.add(collection)
            session.commit()
            return collection.id

    def save_request(self, collection_id, name, method, url, headers=None, body=None):
        """Save a request to a collection."""
        with self.Session() as session:
            request = SavedRequest(
                collection_id=collection_id,
                name=name,
                method=method,
                url=url,
                headers=headers,
                body=body
            )
            session.add(request)
            session.commit()
            return request.id

    def get_collections(self):
        """Get all collections with their requests."""
        with self.Session() as session:
            return session.query(Collection).all()

    def get_collection(self, collection_id):
        """Get a specific collection and its requests."""
        with self.Session() as session:
            return session.query(Collection).filter(Collection.id == collection_id).first()

    def delete_collection(self, collection_id):
        """Delete a collection and all its requests."""
        with self.Session() as session:
            collection = session.query(Collection).filter(Collection.id == collection_id).first()
            if collection:
                session.delete(collection)
                session.commit()
                return True
            return False