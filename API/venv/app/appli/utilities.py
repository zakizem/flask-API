#coding=utf-8
from flask import Flask, render_template, request, jsonify, make_response, session, redirect, flash
import pyorient, yaml, graphene, json, io
from appli.model import *
from functools import wraps

def deleteFile(filename, subfolder):
    print('à faire')

def Existe(attribut ,valeur):
    resultat=chercherBDD('Personne', attribut, valeur)
    if resultat!=[]:
        return True
    return False

def authentification(data):
    if all (k in data for k in ("email","password")):
        resultat=chercherBDD('Personne', 'email', data['email'])
        if resultat!=[]:
            if 'password' in resultat and resultat['password']==data['password']:
                return 'authentification réussie'
            return 'Mauvais mot de passe'
        return "L'adresse mail n'existe pas"
    return "Merci de remplir les champs"

def signup(data):
    if all (k in data for k in ("email","password")):
        if Existe('email ',data['email']):
            return 'Le mail existe déja', 401     # Ajouter status
        # faire des tests d'intégrité des emails et mdp ?
        SauvgarderDoc({'email' : data['email'], 'password': data['password']}, 'Personne')
        return 'fait', 200                       # Ajouter status
    return 'Merci de remplir les champs', 401     # Ajouter status

######### avant API (il y en a qui sont toujours utilisées):

def lireDuFichier(fichier):
    with open(fichier, 'r') as stream:
        data_loaded = yaml.load(stream)

    # print ("Nom des questions unique dans le formulaire ? ")
    # print(nomUniqueFormulaire(data_loaded))

    return data_loaded


# def login_required(f):
#     @wraps(f)
#     def wrap(*args, **kwargs):
#         if 'session_valide' in session:  #and session['session_valide']:
#             flash("Accès autorisé")
#             return f(*args, **kwargs)
#         else:
#             flash("Vous avez besoin de vous authentifier")
#             return redirect ('/')
#     return wrap

# def validation_identifiants(email, password):
#     resultat=chercherBDD('Personne','email', email)
#     if len(resultat) > 0:
#         if resultat[0].oRecordData['password'] == password:
#             return resultat[0].oRecordData
#         return('Mot de passe non valide')
#     return('Email non trouvé')

# def setSession(resultat_validation):
#     session['prenom']=resultat_validation['prenom']
#     session['nom']=resultat_validation['nom']
#     session['email']=resultat_validation['email']
#     session['password']=resultat_validation['password']
#     session['session_valide']=True
#     # session['tout']=resultat_validation
#
# def session_validation():
#     if 'email' in session and 'password' in session and 'prenom' in session:
#         resultat_validation=validation_identifiants(session['email'], session['password'])
#         if type(resultat_validation) != str:
#             session['session_valide']=True
#             return resultat_validation
#     return ("pas de session")

# def return_form():
#     return render_template("formulaire.html", formulaire=lireDuFichier('formulaire_config_questions.yaml'), prerempli=prerempli, update='' )
#     # FAUT GERER LE UPDATE, SINON CE N'EST PAS LA PEINE     # A VOIR

def est_un_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def ecrireDansFichier(data,fichier):
    with io.open(fichier, 'w', encoding='utf8') as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)

def nomUniqueFormulaire(data):
    for elem in data:
        # print('elem : ')
        # print(elem)
        for id_1, element_1 in enumerate(data[elem]):
            for id_2, element_2 in enumerate(data[elem]):
                if id_1 != id_2:
                    if element_1['nom_de_la_question'] == element_2['nom_de_la_question']:
                        return False
    return True         # Voir comment traiter les exceptions ?

# def conversionLisibleJinja(data):
#     return yaml.load(yaml.dump(data))      # ou : parcourir le requestData avec for in de python, tout mettre en String, puis convertir en Json
#
# def nettoyerData(data):
#     for element in data:
#         if '' == data[element]:
#             del data[element]
#     return data                   # non utilisée
