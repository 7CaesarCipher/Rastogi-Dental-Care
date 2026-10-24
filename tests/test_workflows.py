"""Integration tests for core clinical/research guardrails and role authorization."""
import os
import tempfile
from pathlib import Path

os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.mkdtemp()) / 'test.db')
os.environ['DEMO_SEED'] = 'true'
from fastapi.testclient import TestClient
from app.main import app


def login(client, who='admin'):
    response=client.post('/api/login', json={'username':who,'password':'Demo@12345'})
    assert response.status_code == 200, response.text


def test_app_boot_health_and_assets():
    with TestClient(app) as c:
        assert c.get('/api/health').json()['compliance_validated'] is False
        assert c.get('/').status_code == 200
        assert c.get('/static/app.css').status_code == 200
        assert c.get('/static/app.js').status_code == 200
        assert c.get('/api/patients').status_code == 401
        login(c)
        result = c.get('/api/summary').json()
        assert result['patients'] >= 3
        assert result['trials'] >= 1


def test_dental_care_lifecycle_and_permissions():
    with TestClient(app) as c:
        login(c, 'dentist')
        r = c.post('/api/patients',json={'name':'Test Patient A','dob':'1990-01-01','gender':'Other'})
        assert r.status_code==200,r.text
        patient_id=r.json()['id']
        bad = c.post('/api/findings',json={'patient_id':patient_id,'tooth':'99','finding':'Caries'})
        assert bad.status_code == 422
        good = c.post('/api/findings',json={'patient_id':patient_id,'tooth':'36','finding':'Caries','probing_mm':4})
        assert good.status_code == 200
        plan = c.post('/api/care-plans',json={'patient_id':patient_id,'tooth':'36','diagnosis':'Occlusal caries','procedure':'Composite restoration'})
        assert plan.status_code==200,plan.text
        plan_id=plan.json()['id']
        procedure={'patient_id':patient_id,'plan_id':plan_id,'performed_on':'2026-10-24','clinician':'Dr. Test','performed':'Composite restoration'}
        assert c.post('/api/procedures',json=procedure).status_code==409
        assert c.post(f'/api/care-plans/{plan_id}/status',json={'status':'APPROVED'}).status_code==200
        treatment=c.post('/api/procedures',json=procedure)
        assert treatment.status_code==200,treatment.text
        assert c.post(f'/api/care-plans/{plan_id}/status',json={'status':'COMPLETED'}).status_code==200
        assert c.post(f'/api/care-plans/{plan_id}/status',json={'status':'DRAFT'}).status_code==409
        # Dentist must not be able to change EC/registry trial state or billing.
        assert c.post('/api/invoices',json={'patient_id':patient_id,'description':'test','amount':10,'created_on':'2026-10-24'}).status_code==403
        assert c.get('/api/audit').status_code==403


def test_research_consent_screening_enrollment_and_withdrawal():
    with TestClient(app) as c:
        login(c,'admin')
        pat=c.post('/api/patients',json={'name':'Fictional Research Subject','dob':'1987-06-01'}).json()
        pid=pat['id']
        code='DEMO-TEST-NEW'
        r=c.post('/api/trials',json={'code':code,'title':'Test of Dental Treatment Results','indication':'Gum disease',
                                      'intervention':'Care protocol','regulatory_required':True})
        assert r.status_code==200,r.text
        tid=r.json()['id']
        enroll={'patient_id':pid,'trial_id':tid,'enrolled_on':'2026-10-24'}
        assert c.post('/api/enrollments',json=enroll).status_code==409
        assert c.post(f'/api/trials/{tid}/status',json={'status':'EC_APPROVED'}).status_code==409
        assert c.post(f'/api/trials/{tid}/status',json={'status':'EC_APPROVED','ec_reference':'EXTERNAL-DEMO-EC'}).status_code==200
        assert c.post(f'/api/trials/{tid}/status',json={'status':'ACTIVE','registry_reference':'TEST-REGISTER-ONLY'}).status_code==409
        assert c.post(f'/api/trials/{tid}/status',json={'status':'ACTIVE','registry_reference':'TEST-REGISTER-ONLY','regulatory_reference':'TEST-REGULATOR-ONLY'}).status_code==200
        screen={'patient_id':pid,'trial_id':tid,'screened_on':'2026-10-21','eligibility':'ELIGIBLE','inclusion_exclusion_notes':'Criteria reviewed by investigator','reviewer':'Reviewer'}
        assert c.post('/api/screenings',json=screen).status_code==409
        consent={'patient_id':pid,'trial_id':tid,'signed_on':'2026-10-20','obtained_by':'Investigator',
                 'document_version':'1.0','document_reference':'EXTERNAL-ICF-TEST','verified':True}
        assert c.post('/api/consents',json={**consent,'verified':False}).status_code==422
        r=c.post('/api/consents',json=consent)
        assert r.status_code==200,r.text
        consent_id=r.json()['id']
        assert c.post('/api/enrollments',json=enroll).status_code==409
        assert c.post('/api/screenings',json=screen).status_code==200
        r=c.post('/api/enrollments',json=enroll)
        assert r.status_code==200,r.text
        eid=r.json()['id']
        r=c.post('/api/research-visits',json={'enrollment_id':eid,'visit_name':'Baseline','visit_on':'2026-10-24','probing_mm':3.8,'dmft':4})
        assert r.status_code==200,r.text
        ae=c.post('/api/safety-events',json={'enrollment_id':eid,'onset_on':'2026-10-24','description':'Test serious event','serious':True,'severity':'Severe'})
        assert ae.status_code==200
        aeid=ae.json()['id']
        assert c.post(f'/api/safety-events/{aeid}/status',json={'status':'CLOSED'}).status_code==409
        assert c.post(f'/api/safety-events/{aeid}/status',json={'status':'REPORTED','reported_on':'2026-10-24'}).status_code==200
        assert c.post(f'/api/consents/{consent_id}/withdraw',json={}).status_code==200
        assert c.post('/api/research-visits',json={'enrollment_id':eid,'visit_name':'Week 1','visit_on':'2026-10-26'}).status_code==409


def test_role_blocks_research_operations():
    with TestClient(app) as c:
        login(c,'frontdesk')
        assert c.post('/api/trials',json={'code':'BLOCK','title':'Blocked Test Trial','indication':'Gums','intervention':'Test'}).status_code==403
        assert c.post('/api/findings',json={'patient_id':1,'tooth':'36','finding':'Caries'}).status_code==403
        assert c.get('/api/patients').status_code==200
        assert c.get('/api/audit').status_code==403


def test_operations_and_payment_guards():
    with TestClient(app) as c:
        login(c, 'admin')
        patient_id=c.post('/api/patients',json={'name':'Fictional Payment Record','dob':'1998-07-20'}).json()['id']
        invoice=c.post('/api/invoices',json={'patient_id':patient_id,'description':'Dental service demo',
                                               'amount':1500,'paid':500,'created_on':'2026-10-24'})
        assert invoice.status_code==200,invoice.text
        iid=invoice.json()['id']
        assert c.post(f'/api/invoices/{iid}/pay',json={'amount':1001}).status_code==409
        assert c.post(f'/api/invoices/{iid}/pay',json={'amount':1000}).json()['paid']==1500
        stock=c.post('/api/stock',json={'name':'Test instrument pack','category':'Sterilization','quantity':4,'reorder_point':2})
        assert stock.status_code==200
        sid=stock.json()['id']
        assert c.post(f'/api/stock/{sid}/use',json={'amount':5,'purpose':'Dental procedure'}).status_code==409
        assert c.post(f'/api/stock/{sid}/use',json={'amount':2,'purpose':'Dental procedure'}).json()['quantity']==2
        appt=c.post('/api/appointments',json={'patient_id':patient_id,'scheduled_at':'2026-10-27T09:30',
                                               'provider':'Dr Example','purpose':'Review'})
        assert appt.status_code==200
        assert c.post(f"/api/appointments/{appt.json()['id']}/status",json={'status':'Checked in'}).status_code==200


def test_signup_pending_approval_and_server_side_permissions():
    with TestClient(app) as staff, TestClient(app) as admin:
        account = {'username': 'new.dentist', 'display_name': 'New Staff Dentist',
                   'requested_role': 'dentist', 'password': 'SecurePass2026!',
                   'confirm_password': 'SecurePass2026!'}
        assert staff.post('/api/signup', json={**account, 'requested_role': 'admin'}).status_code == 422
        assert staff.post('/api/signup', json={**account, 'confirm_password': 'Mismatch2026!'}).status_code == 422
        registered = staff.post('/api/signup', json=account)
        assert registered.status_code == 201, registered.text
        assert registered.json()['status'] == 'PENDING'
        assert staff.post('/api/signup', json=account).status_code == 409
        assert staff.post('/api/login', json={'username': 'new.dentist', 'password': account['password']}).status_code == 403
        login(admin)
        assert admin.get('/api/admin/catalog').status_code == 200
        target = next(x for x in admin.get('/api/admin/users').json() if x['username'] == 'new.dentist')
        uid = target['id']
        assert target['status'] == 'PENDING'
        assert target['requested_role'] == 'dentist'
        assert 'pw_hash' not in str(target)
        assert admin.post(f'/api/admin/users/{uid}/review', json={'role':'dentist', 'status':'ACTIVE'}).status_code == 200
        r = staff.post('/api/login', json={'username': 'new.dentist', 'password': account['password']})
        assert r.status_code == 200
        assert r.json()['permissions']['patients']['write'] is True
        assert r.json()['permissions']['trials']['view'] is True
        assert r.json()['permissions']['consents']['view'] is False
        assert staff.get('/api/patients').status_code == 200
        assert staff.get('/api/consents').status_code == 403
        assert staff.get('/api/admin/users').status_code == 403
        assert staff.post('/api/trials', json={'code':'MAY-NOT-CREATE','title':'Not allowed trial', 'indication':'X', 'intervention':'Y'}).status_code == 403
        # Admin can deny one page and provide view-only access to another.
        assert admin.post(f'/api/admin/users/{uid}/permission', json={'module':'patients','access':'none'}).status_code == 200
        assert staff.get('/api/patients').status_code == 401  # session revoked
        assert staff.post('/api/login', json={'username':'new.dentist','password':account['password']}).status_code == 200
        assert staff.get('/api/patients').status_code == 403
        assert admin.post(f'/api/admin/users/{uid}/permission', json={'module':'patients','access':'read'}).status_code == 200
        assert staff.post('/api/login', json={'username':'new.dentist','password':account['password']}).status_code == 200
        assert staff.get('/api/patients').status_code == 200
        assert staff.post('/api/patients', json={'name':'Forbidden Creation','dob':'2000-01-01'}).status_code == 403
        assert admin.post(f'/api/admin/users/{uid}/permission', json={'module':'trials','access':'write'}).status_code == 200
        assert staff.post('/api/login', json={'username':'new.dentist','password':account['password']}).status_code == 200
        assert staff.post('/api/trials', json={'code':'NEW-STAFF-PROTO','title':'Permitted Protocol Demo', 'indication':'Dentistry', 'intervention':'X'}).status_code == 200
        # EC approval is a protected administrative workflow, not delegated with write permission.
        tid = admin.get('/api/trials').json()[0]['id']
        assert staff.post(f'/api/trials/{tid}/status', json={'status':'EC_APPROVED','ec_reference':'UNTRUSTED'}).status_code == 403
        assert admin.post(f'/api/admin/users/{uid}/permission', json={'module':'audit','access':'read'}).status_code == 422
        assert admin.post(f'/api/admin/users/{uid}/permission', json={'module':'users','access':'write'}).status_code == 422
        assert admin.post(f'/api/admin/users/{uid}/permission', json={'module':'patients','access':'default'}).status_code == 200
        updated = next(x for x in admin.get('/api/admin/users').json() if x['id'] == uid)
        assert updated['permissions']['patients']['write'] is True
        assert 'patients' not in updated['overrides']
        assert admin.post(f'/api/admin/users/{uid}/review', json={'role':'dentist','status':'SUSPENDED'}).status_code == 200
        assert staff.get('/api/trials').status_code == 401
        assert staff.post('/api/login', json={'username':'new.dentist','password':account['password']}).status_code == 403


def test_role_specific_read_permissions_and_admin_protections():
    with TestClient(app) as client:
        login(client, 'frontdesk')
        me = client.get('/api/me').json()
        assert me['permissions']['appointments']['write']
        assert not me['permissions']['trials']['view']
        assert client.get('/api/trials').status_code == 403
        assert client.get('/api/research-visits').status_code == 403
        assert client.get('/api/invoices').status_code == 200
        assert client.get('/api/summary').json()['trials'] is None
        assert client.get('/api/admin/users').status_code == 403
        login(client, 'researcher')
        assert client.get('/api/patients').status_code == 200
        assert client.post('/api/patients', json={'name':'Not Allowed','dob':'2000-01-01'}).status_code == 403
        assert client.get('/api/invoices').status_code == 403
        assert client.post('/api/signup',json={'username':'aaa','display_name':'A', 'requested_role':'admin','password':'Pass2026pass','confirm_password':'Pass2026pass'}).status_code == 422
        login(client, 'admin')
        myself = client.get('/api/me').json()['id']
        assert client.post(f'/api/admin/users/{myself}/review',json={'role':'receptionist','status':'SUSPENDED'}).status_code == 409
        assert client.post(f'/api/admin/users/{myself}/permission',json={'module':'dashboard','access':'none'}).status_code == 409
