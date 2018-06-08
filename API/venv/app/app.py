#coding=utf-8
from flask import Flask, render_template, request, jsonify, make_response, session, redirect, flash
import pyorient, yaml, graphene, json, io
from pyorient.ogm import Graph, Config, declarative
from pprint import pprint
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.datastructures import ImmutableMultiDict
import jwt
import datetime
from functools import wraps

from appli.utilities import *
from appli.model import *
from appli.form import *
from appli.traitementExceptions import *


import rethinkdb as r

## API rest

from flask_restful import Resource, Api
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

api = Api(app)

app.config['SECRET_KEY'] = 'une_clé_secrète'

# cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


## API rest


# app.secret_key = 'clé_secrète'            # à terme, utiliser un générateur auto de secret keys

app.register_blueprint(traitementExceptions)

# the toolbar is only enabled in debug mode:
app.debug = True
# set a 'SECRET_KEY' to enable the Flask session cookies
# app.config['SECRET_KEY'] = 'une_clé_secrète'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)



@app.route('/')
def index():
    #return ('API en marche..')
    return render_template("vueJS/index.html")



##### API avec flask_restful

class Questions(Resource):
    def get(self):
        data= lireDuFichier('formulaire_config_questions.yaml')
        return jsonify(data)

class Reponses(Resource):
    def post(self):
        data=request.get_json()
        if 'email' in data:
            if Existe('email ',data['email']):
                return 'Le mail existe déja'
            SauvgarderDoc(data, 'Personne')
            resultat=chercherBDD('Personne','email', data['email'])
            return resultat

class Authentification(Resource):
    def post(self):

        data = request.get_json()

        auth = authentification(data)
        if auth == 'authentification réussie':
            token = jwt.encode({'user' : data['email'], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=1)}, app.config['SECRET_KEY'])
            return jsonify({'token' : token.decode('UTF-8')})
        return auth

        # return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

        # à la base c'était :
        # data=request.get_json()
        # return authentification(data)

api.add_resource(Questions, '/1')
api.add_resource(Reponses, '/envoi')
api.add_resource(Authentification, '/authentification')

##### API

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') #http://127.0.0.1:5000/route?token=alshfjfjdklsfj89549834ur

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 403

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message' : 'Token is invalid!'}), 403

        return f(*args, **kwargs)

    return decorated



@app.route('/unprotected')
def unprotected():
    return jsonify({'message' : 'Anyone can view this!'})

@app.route('/protected')
@token_required
def protected():
    return jsonify({'message' : 'This is only available for people with valid tokens.'})

@app.route('/login')
def login():
    auth = request.authorization
    if auth and auth.password == 'secret':
        token = jwt.encode({'user' : auth.username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(seconds=15)}, app.config['SECRET_KEY'])
        return jsonify({'token' : token.decode('UTF-8')})
    return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})



# @app.route('/1')
# def index1():
#     data= lireDuFichier('formulaire_config_questions.yaml')
#     return jsonify(data)

@app.route('/identification', methods=['POST'])
def identification():
    resultat_validation=validation_identifiants(request.form['email_accueil'], request.form['password_accueil'])
    if(type(resultat_validation)) == str:
        return resultat_validation
    setSession(resultat_validation)
    return redirect('/form')


@app.route('/2', methods=['POST'])
def envoi1():
    SauvgarderDoc(request.form, 'Personne')
    resultat=chercherBDD('Personne','nom', request.form['nom'])
    # resultatMultiple=chercherBDDmultiple('Personne', requete)
    return('fait ! ')
    # return render_template("resultat.html",resultat=resultat, questions=lireDuFichier('formulaire_config_questions.yaml'))


@app.route('/testdata', methods=['POST'])
def testdata():
    print('Données reçues : ')
    print(request.form)


##### FIN API
















@app.route('/form')
def form():
    resultat_validation=session_validation()
    if type(resultat_validation) != str:
        prerempli=resultat_validation
        update='Update'
    else:
        prerempli={}
        update=''
    return render_template("formulaire.html", formulaire=lireDuFichier('formulaire_config_questions.yaml'), prerempli=prerempli, update=update )

# @app.route('/envoi', methods=['POST'])
# def envoi():
#     SauvgarderDoc(request.form, 'Personne')
#     resultat=chercherBDD('Personne','nom', request.form['nom'])
#     # resultatMultiple=chercherBDDmultiple('Personne', requete)
#     return render_template("resultat.html",resultat=resultat, questions=lireDuFichier('formulaire_config_questions.yaml'))

@app.route('/envoiUpdate', methods=['POST'])
def envoiUpdate():
    resultat = update('Personne')
    if type(resultat) == str:
        return resultat
    setSession(session_validation())     #Reremplir la variable session
    return render_template("resultat.html",resultat=resultat, questions=lireDuFichier('formulaire_config_questions.yaml'))

@app.route('/identificationOLD', methods=['POST'])
def identificationOLD():
    resultat_validation=validation_identifiants(request.form['email_accueil'], request.form['password_accueil'])
    if(type(resultat_validation)) == str:
        return resultat_validation
    setSession(resultat_validation)
    return redirect('/form')
    # return render_template("formulaire.html", formulaire=lireDuFichier('formulaire_config_questions.yaml'), prerempli=resultat_validation, update='Update')

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect('/')

@app.route('/_envoi_ajax')
def envoi_ajax():
    email = request.args.get('email')

    resultat=chercherBDD('Personne','email', email)

    print("resultat recherche : ")
    print(resultat)

    if resultat == []:
        mail_existe = False
    else:
        mail_existe = True

    print(email)
    return jsonify(ajax_result='salut '+email, mail_existe=mail_existe)

@app.route('/decorateur')
@login_required
def decorateur():
    return redirect ('/')

@app.route('/testRethink')
def testRethink():
    r.connect( "localhost", 28015).repl()

    # r.db("test").table_create("authors").run()

    r.table("authors").insert([
        { "name": "William Adama", "tv_show": "Battlestar Galactica",
          "posts": [
            {"title": "Decommissioning speech", "content": "The Cylon War is long over..."},
            {"title": "We are at war", "content": "Moments ago, this ship received..."},
            {"title": "The new Earth", "content": "The discoveries of the past few days..."}
          ]
        },
        { "name": "Laura Roslin", "tv_show": "Battlestar Galactica",
          "posts": [
            {"title": "The oath of office", "content": "I, Laura Roslin, ..."},
            {"title": "They look like us", "content": "The Cylons have the ability..."}
          ]
        },
        { "name": "Jean-Luc Picard", "tv_show": "Star Trek TNG",
          "posts": [
            {"title": "Civil rights", "content": "There are some words I've known since..."}
          ]
        }
    ]).run()

    cursor = r.table("authors").run()
    for document in cursor:
        print(document)

    return("fait")


########### wtforms


@app.route('/wtforms', methods=['GET', 'POST'])
def wtforms():
    render_template('formWTForms.html',form=form, formulaire=lireDuFichier('formulaire_config_questions.yaml'), prerempli='')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        # user = User(form.username.data, form.email.data,
        #             form.password.data)
        # print("userrrrrrrr")
        # print(user)   ### Enregistrement BDD - Remplir Session maybe ?
        flash('Thanks for registering')
        return render_template('formWTForms.html', form=form, formulaire=lireDuFichier('formulaire_config_questions.yaml'), prerempli='')
        # return redirect(url_for('accueil'))
    flash("non")
    return render_template('formWTForms.html', form=form, formulaire=lireDuFichier('formulaire_config_questions.yaml'), prerempli='')


##############

#
# @app.errorhandler(404)
# def page_not_found(e):
#     return("ERREUR 400000000000000004 !!!!")


##############


requete = {'nom': 'Aladin', 'destination': 'Turin'}

formulaire = [
    {
        'type': 'email',
        'nom_de_la_question': 'email',
        'text': 'Adresse mail : '
    },
    {
        'type': 'text',
        'nom_de_la_question': 'password',
        'text': 'Mot de passe : '
    },
    {
        'type': 'text',
        'nom_de_la_question': 'prenom',
        'text': 'prenom : '
    },
    {
        'type': 'text',
        'nom_de_la_question': 'nom',
        'text': 'Nom : '
    },
    {
        'type': 'liste',
        'nom_de_la_question': 'destination',
        'text': 'Destination de vacances favorite : ',
        'choix': ['Budapest', 'Amsterdam', 'Turin', 'Bamako']
    },
    {
        'type': 'text',
        'nom_de_la_question': 'age',
        'text': 'Age : ',
        'commentaire': 'Commentaire'
    }
]
# ecrireDansFichier(formulaire,'formulaire_config_questions.yaml')

#############

if __name__ == "__main__":
    print (__name__)
    app.run(host="127.0.0.1", port=5000, threaded=True)