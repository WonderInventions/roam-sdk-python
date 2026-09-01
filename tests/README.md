# Contract tests

Hand-written tests that pin generated client behavior. HTTP is faked with
`httpx.MockTransport` against `https://api.ro.am/v1`. An unhandled request
fails the test rather than hitting the network.

`webhook_verify_test.py` covers the hand-written verifier and runs against
the seed tree (no generated client required). Pagination / version / retry
tests land once the generated client is installed.
