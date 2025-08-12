import http from 'k6/http';
import {sleep,check} from 'k6';

//define http requests that you would like to test

export let options = { 
    stages: [
        { duration: '10s', target:800 },   
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests should complete within 500ms
        http_req_failed: ['rate<0.05'],   // Failures should be below 5%
    },
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(50)', 'p(90)', 'p(95)', 'p(99)'],
};


const BASE_URL= 'http://127.0.0.1:8000/api/v2' ;
// const BASE_URL = 'https://url-shortener-api-sekf.onrender.com'
const TEST_URLL= "https://example.com" ;
const TESTT_URL="https://fastapi.tiangolo.com/advanced/async-tests/#run-it";
const TEST_URL="https://docs.sqlalchemy.org/en/20/core/constraints.html" ;
const testt_url="https://githubuniverse.com/";
const get_return_url="https://grafana.com/docs/k6/latest/testing-guides/test-types/stress-testing/"
const test_url="https://leetcode.com/studyplan/top-interview-150/"

const faze_url="https://www.isavellatsoulias.com/understanding-phage-therapy"


export default function(){

    // post endpoint test

    // const randomIndex = Math.floor(Math.random() * TEST_URLS.length);
    // const TEST_URL = TEST_URLS[randomIndex];
    // const uniqueId = __VU; // __VU is the unique ID of the current virtual user
    // const TEST_URL = `${TEST_URLL}/${uniqueId}`; 

    // let postPayload = JSON.stringify({url_link:faze_url}) //Javacript value to JSON string
    // let postHeaders = {'Content-Type':'application/json',
    //     'Authorization':'Bearer hCxN5ak5h-5CkDN6bEz72WpM5n43MHioVlfcx_sa80E'} ;
    // let postres = http.post(`${BASE_URL}/shorten`,postPayload,{headers:postHeaders})
    // // // console.log(postres.json("short_url"))
    // check(postres,{
    //     "response code was 200": (postres)=>postres.status==200,
    //     "short_url is returned": (postres)=>postres.json("short_url") !==undefined && postres.json("short_url") !==null 
    //     }
    // )

    // || console.error("Request failed or database conn not available");

    // let short_code = postres.json("short_url");

    // get endpoint test

    // let short_code="something" 

    // let getHeaders = {'Content-Type':'application/json',
    //     'api-key':'wrogkey'}; // intentionally wrong api key to test auth failure;

    
    // let getres = http.get(`${BASE_URL}/redirect?short_code=something`, {headers: getHeaders});
    // check(getres, {
    //     "auth failed (401 or 403)": (r) => r.status === 403 || r.status === 401
    // });

    let getres=http.get(`${BASE_URL}/redirect?short_code=faze`,{redirects:0});
    check(getres,{
        "response code was 307": (getres)=>getres.status===307,
        "redirection is correct" : (getres) =>getres.headers['Location']===faze_url
    });

    sleep(1);

}