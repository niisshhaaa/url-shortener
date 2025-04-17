import http from 'k6/http';
import {sleep,check} from 'k6';

//define http requests that you would like to test

export let options = { 
    stages: [
        { duration: '30s', target:800 },   
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests should complete within 500ms
        http_req_failed: ['rate<0.05'],   // Failures should be below 5%
    },
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(50)', 'p(90)', 'p(95)', 'p(99)'],
};


const BASE_URL= 'http://127.0.0.1:8000' ;
// const BASE_URL = 'https://url-shortener-api-sekf.onrender.com'
const TEST_URLL= "https://example.com" ;
const TESTT_URL="https://fastapi.tiangolo.com/advanced/async-tests/#run-it";
const TEST_URL="https://docs.sqlalchemy.org/en/20/core/constraints.html" ;
const testt_url="https://githubuniverse.com/";
const get_return_url="https://grafana.com/docs/k6/latest/testing-guides/test-types/stress-testing/"
const test_url="https://leetcode.com/studyplan/top-interview-150/"


export default function(){

    // post endpoint test

    // const randomIndex = Math.floor(Math.random() * TEST_URLS.length);
    // const TEST_URL = TEST_URLS[randomIndex];
    // const uniqueId = __VU; // __VU is the unique ID of the current virtual user
    // const TEST_URL = `${TEST_URLL}/${uniqueId}`; 

    let postPayload = JSON.stringify({url_link:test_url}) //Javacript value to JSON string
    let postHeaders = {'Content-Type':'application/json',
        'api-key':'NtI8xTE2_M9T8AistPV4I165QwwpN4th4SdEtfbITFs'} ;
    let postres = http.post(`${BASE_URL}/shorten`,postPayload,{headers:postHeaders})
    // console.log(postres.json("short_url"))
    check(postres,{
        "response code was 200": (postres)=>postres.status==200,
        "short_url is returned": (postres)=>postres.json("short_url") !==undefined && postres.json("short_url") !==null 
        }
    )

    // || console.error("Request failed or database conn not available");

    // let short_code = postres.json("short_url");

    // get endpoint test

    // let short_code="something" 

    // let getres=http.get(`${BASE_URL}/redirect?short_code=something`,{redirects:0});
    // check(getres,{
    //     "response code was 307": (getres)=>getres.status===307,
    //     "redirection is correct" : (getres) =>getres.headers['Location']===get_return_url
    // });

    sleep(1);

}