
from backend.main import app
import pytest
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.mark.anyio
async def test_post():
    async with LifespanManager(app):
         input_url="https://docs.sqlalchemy.org/en/20/core/constraints.html"
         async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

            post_response=await ac.post('/shorten',json={"url_link":input_url,"custom_slug":None,"exp_date":None},headers={"api-key":"hCxN5ak5h-5CkDN6bEz72WpM5n43MHioVlfcx_sa80E"})
            assert post_response.status_code == 200 
            assert post_response.json() is not None

            response_invalid_userkey=await ac.post('/shorten',json={"url_link":input_url,"custom_slug":None,"exp_date":None},headers={"api-key":"hCxN5ak5h-5CkDN6bEz"})
            assert response_invalid_userkey.status_code == 403
            assert response_invalid_userkey.json()=={"detail":"Not a valid api key"}

            response_invalid_url=await ac.post('/shorten',json={"url_link":"","custom_slug":None,"exp_date":None},headers={"api-key":"hCxN5ak5h-5CkDN6bEz72WpM5n43MHioVlfcx_sa80E"})
            assert response_invalid_url.status_code == 400
            assert response_invalid_url.json()=={"detail":"Invalid or insecure URL format"}

            correct_form_exp=await ac.post('/shorten',json={"url_link":input_url,"exp_date":"2025-02-01"},headers={"api-key":"hCxN5ak5h-5CkDN6bEz72WpM5n43MHioVlfcx_sa80E"})
            assert correct_form_exp.status_code == 200 
            assert correct_form_exp.json() is not None

            # custome_slug_unq=await ac.post('/shorten',json={"url_link":input_url,"custom_slug":"sqlcotre"},headers={"api-key":"NtI8xTE2_M9T8AistPV4I165QwwpN4th4SdEtfbITFs"})
            # assert custome_slug_unq.status_code == 200 
            # assert custome_slug_unq.json() is not None

            custome_slug_nonunq=await ac.post('/shorten',json={"url_link":input_url,"custom_slug":"sqalconsre"},headers={"api-key":"NtI8xTE2_M9T8AistPV4I165QwwpN4th4SdEtfbITFs"})
            assert custome_slug_nonunq.status_code== 409 
            assert custome_slug_nonunq.json() =={"detail":"Code already exits, Retry"}

            enterprise_user=await ac.post('/shorten',json=[{"url_link":input_url,"custom_slug":None,"exp_date":None},{"url_link":input_url,"custom_slug":"sqalconsre","exp_date":None}],
                          headers={"api-key":"hCxN5ak5h-5CkDN6bEz72WpM5n43MHioVlfcx_sa80E"})
            assert enterprise_user.status_code == 200 
            assert enterprise_user.json()["successes"] is not None
            assert enterprise_user.json()["failures"] is not None

            hobby_user=await ac.post('/shorten',json=[{"url_link":input_url,"custom_slug":None,"exp_date":None},{"url_link":input_url,"custom_slug":"sqalconsre","exp_date":None}],
                          headers={"api-key":"EcRGiU5nK8e90-eBMT2k-abcoEsZPYw9bTmcw_V6O8w"})
            assert hobby_user.status_code == 400
            assert hobby_user.json()=={"detail":"Invalid request for Hobby tier without pricing"}
    

          
@pytest.mark.anyio      
async def test_get():  
       async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            short_code="1e1052"
            input_url="https://grafana.com/docs/k6/latest/extensions/"
            get_response=await ac.get(f'/redirect?short_code={short_code}',follow_redirects=False)
            assert get_response.status_code == 307
            get_res=get_response.headers["Location"]
            assert get_res==input_url
            
            incorrect_scode="codedoesnotexist"
            get_response2=await ac.get(f'/redirect?short_code={incorrect_scode}',follow_redirects=False)
            assert get_response2.status_code == 404
            assert get_response2.json()== {"detail":"URL not found"}

            expired_code="e8b00d2e6"
            expired_code_res=await ac.get(f'/redirect?short_code={expired_code}',follow_redirects=False)
            assert expired_code_res.status_code==410
            assert expired_code_res.json()=={"detail":"Code already expired"}


@pytest.mark.anyio      
async def test_del():
       async with LifespanManager(app):  
           async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
              
              response_invalid_key = await ac.delete(f"/shorten/cd6f68a",headers={"api-key":"yyyy"})
              assert response_invalid_key.status_code == 403
              assert response_invalid_key.json()=={"detail":"Not a valid api key"}
              

              incorrect_scode="incorrect_code"
              response_invalid_scode = await ac.delete(f"/shorten/{incorrect_scode}",headers={"api-key":"EcRGiU5nK8e90-eBMT2k-abcoEsZPYw9bTmcw_V6O8w"})
              assert response_invalid_scode.status_code == 404
              assert response_invalid_scode.json()=={"detail":"Not a valid short code"}
              
            #   code_to_del="68a4d434"
            #   del_response=await ac.delete(f'/shorten/{code_to_del}',headers={"api-key":"EcRGiU5nK8e90-eBMT2k-abcoEsZPYw9bTmcw_V6O8w"})
            #   assert del_response.status_code==200
            #   assert del_response.json()== f"{code_to_del} short code has been deleted"

              code_already_deleted=await ac.delete(f'/shorten/ecdd57',headers={"api-key":"EcRGiU5nK8e90-eBMT2k-abcoEsZPYw9bTmcw_V6O8w"})
              assert code_already_deleted.status_code==410
              assert code_already_deleted.json()=={"detail":"Code already deleted"}

              code_different_user=await ac.delete(f'/shorten/ecdd57',headers={"api-key":"NtI8xTE2_M9T8AistPV4I165QwwpN4th4SdEtfbITFs"})
              assert code_different_user.status_code==403
              assert code_different_user.json()=={"detail":"Cannot delete,Code does not belong to user"}

@pytest.mark.anyio      
async def test_update():
       async with LifespanManager(app):  
           async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
              
              invalid_key = await ac.patch(f"/shorten/sqalexp21?expiry_date=2025-01-28",headers={"api-key":"EcRGiU5nK8e90-"})
              assert invalid_key.status_code == 403
              assert invalid_key.json()=={"detail":"Not a valid api key"}

              code_already_deleted=await ac.patch(f'/shorten/ecdd57?expiry_date=2025-01-28',headers={"api-key":"EcRGiU5nK8e90-eBMT2k-abcoEsZPYw9bTmcw_V6O8w"})
              assert code_already_deleted.status_code==410
              assert code_already_deleted.json()=={"detail":"Code already deleted"}

              incorrect_scode="incorrect_code"
              response_invalid_scode = await ac.patch(f"/shorten/{incorrect_scode}?expiry_date=2025-01-28",headers={"api-key":"EcRGiU5nK8e90-eBMT2k-abcoEsZPYw9bTmcw_V6O8w"})
              assert response_invalid_scode.status_code == 404
              assert response_invalid_scode.json()=={"detail":"Short code not found"}

              code_different_user=await ac.patch(f'/shorten/sqalexp21?expiry_date=2025-01-28',headers={"api-key":"NtI8xTE2_M9T8AistPV4I165QwwpN4th4SdEtfbITFs"})
              assert code_different_user.status_code==403
              assert code_different_user.json()=={"detail":"Cannot update ,code belongs to another user"}

              correctres=await ac.patch(f'/shorten/sqalexp21?expiry_date=2025-01-28&password=wawww',headers={"api-key":"EcRGiU5nK8e90-eBMT2k-abcoEsZPYw9bTmcw_V6O8w"})
              assert correctres.status_code==200
              assert correctres.json()["message"]=="updated short code!"