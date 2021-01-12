import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.db.utils import IntegrityError
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Candidatura, Voting, Question, QuestionOption

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time

class CandidaturaTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
    
    def create_candidatura(self, opcion):
        usuario = User.objects.all()[1]
        if(opcion=="completo"):
            c = Candidatura(nombre="Candidatura completa", delegadoCentro=usuario, representanteDelegadoPrimero=usuario,
            representanteDelegadoSegundo=usuario, representanteDelegadoTercero=usuario, representanteDelegadoCuarto= usuario,
            representanteDelegadoMaster= usuario)
        if(opcion=="nulos"):
            c = Candidatura(nombre="Candidatura con nulos", delegadoCentro=None, representanteDelegadoPrimero=None,
            representanteDelegadoSegundo=None, representanteDelegadoTercero=None, representanteDelegadoCuarto= None,
            representanteDelegadoMaster= None)
        if(opcion=="sinNombre"):
            c = Candidatura(nombre=None, delegadoCentro=usuario, representanteDelegadoPrimero=usuario,
            representanteDelegadoSegundo=usuario, representanteDelegadoTercero=usuario, representanteDelegadoCuarto= usuario,
            representanteDelegadoMaster= usuario)
        c.save()
        return c
    
    def test_create_candidaturaCompleta(self):
        '''test: deja crear candidatura con representantes y delegados'''
        numeroCandidaturas = Candidatura.objects.count()
        c = self.create_candidatura("completo")
        numeroCandidaturasTrasCreate = Candidatura.objects.count()
        self.assertTrue(numeroCandidaturasTrasCreate>numeroCandidaturas)
        self.assertEqual(Candidatura.objects.get(nombre="Candidatura completa").nombre, "Candidatura completa")
        c.delete()
    def test_create_candidaturaSinUsuarios(self):
        '''test: deja crear candidatura sin representantes y delegados'''
        numeroCandidaturas = Candidatura.objects.count()
        c = self.create_candidatura("nulos")
        numeroCandidaturasTrasCreate = Candidatura.objects.count()
        self.assertTrue(numeroCandidaturasTrasCreate>numeroCandidaturas)
        self.assertEqual(Candidatura.objects.get(nombre="Candidatura con nulos").representanteDelegadoCuarto, None)
        c.delete()

    def test_create_candidaturaSinNombre(self):
        '''test: NO deja crear candidatura sin nombre'''
        with self.assertRaises(Exception) as cm:
            self.create_candidatura("sinNombre")
        the_exception = cm.exception
        self.assertEqual(type(the_exception), IntegrityError)

    def test_update_candidatura(self):
        '''test: se puede actualizar una candidatura'''
        c = self.create_candidatura("nulos")
        Candidatura.objects.filter(pk=c.pk).update(nombre="Nombre actualizado")
        c.refresh_from_db()
        self.assertEqual(c.nombre, "Nombre actualizado")
        c.delete()

    def test_delete_candidatura(self):
        '''test: se borra una candidatura'''
        numeroCandidaturas = Candidatura.objects.count()
        c = self.create_candidatura("nulos")
        numeroCandidaturasTrasCreate = Candidatura.objects.count()
        self.assertTrue(numeroCandidaturasTrasCreate>numeroCandidaturas)
        self.assertEqual(Candidatura.objects.get(nombre="Candidatura con nulos").representanteDelegadoCuarto, None)
        c.delete()
        self.assertFalse(Candidatura.objects.filter(nombre="Candidatura con nulos").exists())


class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')

class GeneralVotingTestCase(StaticLiveServerTestCase):

    def setUp(self):
        #Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()    

    def tearDown(self):
        super().tearDown()
        self.driver.quit()
        self.base.tearDown()
    
    def test_view_CreateGeneralVotingOneCandiancyCorrect(self):
        '''test: se crea correctamente la votación general con una candidatura que ha hecho primarias'''
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element(By.ID, "id_username").send_keys("admin")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.LINK_TEXT, "Candidaturas").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_nombre").send_keys("Candidatura de prueba con representantes elegidos")
        select = Select(self.driver.find_element(By.ID, "id_delegadoCentro"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoPrimero"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoSegundo"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoTercero"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoCuarto"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoMaster"))
        select.select_by_visible_text('admin')
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Crear votación general con las candidaturas seleccionadas']").click()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.NAME, "action").click()
        self.driver.find_element(By.NAME, "index").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".success").text == "¡La elección general se ha creado!"
        self.driver.find_element(By.LINK_TEXT, "Voting").click()
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1").text == "Votación general 1"
        self.driver.find_element(By.LINK_TEXT, "Voting").click()
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige a los miembros de delegación de alumnos").text == "Votación general 1: Elige a los miembros de delegación de alumnos"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado al centro").text == "Votación general 1: Elige al delegado al centro"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado del master").text == "Votación general 1: Elige al delegado del master"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de cuarto").text == "Votación general 1: Elige al delegado de cuarto"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de tercero").text == "Votación general 1: Elige al delegado de tercero"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de segundo").text == "Votación general 1: Elige al delegado de segundo"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de primero").text == "Votación general 1: Elige al delegado de primero"
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige a los miembros de delegación de alumnos").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige a los miembros de delegación de alumnos"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado al centro").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado al centro"
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de cuarto").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de cuarto"
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de tercero").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de tercero"
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de segundo").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de segundo"
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de primero").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de primero"
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        self.driver.find_element(By.ID, "id_options-0-option").click()

    def test_view_createGeneralVotingOneCandiancyIncorrect(self):
        '''test: no se crea  la votación general con una candidatura que no ha hecho primarias'''
        self.driver.implicitly_wait(30)
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element(By.ID, "id_username").send_keys("admin")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.LINK_TEXT, "Candidaturas").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_nombre").send_keys("Candidatura de prueba con representantes sin elegir") 
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Crear votación general con las candidaturas seleccionadas']").click()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.NAME, "action").click()
        self.driver.find_element(By.NAME, "index").click()
        self.driver.find_element(By.CSS_SELECTOR, ".error").click()
        self.driver.find_element(By.CSS_SELECTOR, ".error").click()
        element = self.driver.find_element(By.CSS_SELECTOR, ".error")
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        self.driver.find_element(By.CSS_SELECTOR, ".error").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".error").text == "Se ha seleccionado alguna candidatura que no había celebrado votaciones primarias para elegir a los representantes"
            
    def test_view_createGeneralVotingMoreThenOneCandiancyCorrect(self):
        '''test: se crea correctamente la votación general con más de una candidatura que han hecho primarias'''
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element(By.ID, "id_username").send_keys("admin")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.LINK_TEXT, "Candidaturas").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_nombre").send_keys("Candidatura de prueba con representantes elegidos")
        select = Select(self.driver.find_element(By.ID, "id_delegadoCentro"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoPrimero"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoSegundo"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoTercero"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoCuarto"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoMaster"))
        select.select_by_visible_text('admin')
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element(By.LINK_TEXT, "Candidaturas").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_nombre").send_keys("Candidatura de prueba 2 con representantes elegidos")
        select = Select(self.driver.find_element(By.ID, "id_delegadoCentro"))
        select.select_by_visible_text('noadmin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoPrimero"))
        select.select_by_visible_text('noadmin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoSegundo"))
        select.select_by_visible_text('noadmin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoTercero"))
        select.select_by_visible_text('noadmin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoCuarto"))
        select.select_by_visible_text('noadmin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoMaster"))
        select.select_by_visible_text('noadmin')
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.CSS_SELECTOR, ".row2 .action-select").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Crear votación general con las candidaturas seleccionadas']").click()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.NAME, "action").click()
        self.driver.find_element(By.NAME, "index").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".success").text == "¡La elección general se ha creado!"
        self.driver.find_element(By.LINK_TEXT, "Voting").click()
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1").text == "Votación general 1"
        self.driver.find_element(By.LINK_TEXT, "Voting").click()
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige a los miembros de delegación de alumnos").text == "Votación general 1: Elige a los miembros de delegación de alumnos"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado al centro").text == "Votación general 1: Elige al delegado al centro"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado del master").text == "Votación general 1: Elige al delegado del master"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de cuarto").text == "Votación general 1: Elige al delegado de cuarto"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de tercero").text == "Votación general 1: Elige al delegado de tercero"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de segundo").text == "Votación general 1: Elige al delegado de segundo"
        assert self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de primero").text == "Votación general 1: Elige al delegado de primero"
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige a los miembros de delegación de alumnos").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige a los miembros de delegación de alumnos"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado al centro").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado al centro"
        assert self.driver.find_element(By.ID, "id_options-1-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba 2 con representantes elegidos": noadmin_firstname noadmin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        value = self.driver.find_element(By.ID, "id_options-1-number").get_attribute("value")
        assert value == "2"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de cuarto").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de cuarto"
        assert self.driver.find_element(By.ID, "id_options-1-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba 2 con representantes elegidos": noadmin_firstname noadmin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        value = self.driver.find_element(By.ID, "id_options-1-number").get_attribute("value")
        assert value == "2"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de tercero").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de tercero"
        assert self.driver.find_element(By.ID, "id_options-1-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba 2 con representantes elegidos": noadmin_firstname noadmin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        value = self.driver.find_element(By.ID, "id_options-1-number").get_attribute("value")
        assert value == "2"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de segundo").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de segundo"
        assert self.driver.find_element(By.ID, "id_options-1-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba 2 con representantes elegidos": noadmin_firstname noadmin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        value = self.driver.find_element(By.ID, "id_options-1-number").get_attribute("value")
        assert value == "2"
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.LINK_TEXT, "Votación general 1: Elige al delegado de primero").click()
        assert self.driver.find_element(By.ID, "id_desc").text == "Votación general 1: Elige al delegado de primero"
        assert self.driver.find_element(By.ID, "id_options-1-option").text == 'Candidatura "Candidatura de prueba con representantes elegidos": admin_firstname admin_lastname'
        assert self.driver.find_element(By.ID, "id_options-0-option").text == 'Candidatura "Candidatura de prueba 2 con representantes elegidos": noadmin_firstname noadmin_lastname'
        value = self.driver.find_element(By.ID, "id_options-0-number").get_attribute("value")
        assert value == "1"
        value = self.driver.find_element(By.ID, "id_options-1-number").get_attribute("value")
        assert value == "2"

    def test_view_createGeneralVotingMoreThenOneCandiancyIncorrect(self):
        '''test: no se crea la votación general con varias candidatura si una no ha celebrado primarias'''
        self.driver.implicitly_wait(30)
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element(By.ID, "id_username").send_keys("admin")
        self.driver.find_element(By.ID, "id_password").send_keys("qwerty")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.LINK_TEXT, "Candidaturas").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_nombre").send_keys("Candidatura de prueba con representantes elegidos") 
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.get(f'{self.live_server_url}/admin/')
        self.driver.find_element(By.LINK_TEXT, "Candidaturas").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_nombre").send_keys("Candidatura de prueba con representantes elegidos")
        select = Select(self.driver.find_element(By.ID, "id_delegadoCentro"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoPrimero"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoSegundo"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoTercero"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoCuarto"))
        select.select_by_visible_text('admin')
        select = Select(self.driver.find_element(By.ID, "id_representanteDelegadoMaster"))
        select.select_by_visible_text('admin')
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.CSS_SELECTOR, ".row2 .action-select").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Crear votación general con las candidaturas seleccionadas']").click()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.NAME, "action")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.NAME, "action").click()
        time.sleep(2)
        self.driver.find_element(By.NAME, "index").click()
        time.sleep(2)
        element = self.driver.find_element(By.CSS_SELECTOR, ".error")
        actions = ActionChains(self.driver)
        actions.double_click(element).perform()
        self.driver.find_element(By.CSS_SELECTOR, ".error").click()
        time.sleep(2)

        assert self.driver.find_element(By.CSS_SELECTOR, ".error").text == "Se ha seleccionado alguna candidatura que no había celebrado votaciones primarias para elegir a los representantes"