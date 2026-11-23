"""Проверяет статусы HTML-страниц и права через Nginx в Docker Compose."""

import json
from http.cookiejar import CookieJar
from os import environ
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE_URL = environ.get("CABINET_URL", "http://127.0.0.1:5173")


def request(browser, path, *, method="GET", body=None, api=False):
    headers = {"X-Olympiad-Cabinet": "1"} if api else {}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    try:
        response = browser.open(
            Request(BASE_URL + path, data, headers, method=method), timeout=10
        )
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.read(), response.headers


def expect_accounts(browser):
    with browser.open(BASE_URL + "/accounts", timeout=10) as page:
        assert page.status == 200
        assert page.geturl() == BASE_URL + "/accounts"


def main():
    admin = build_opener(HTTPCookieProcessor(CookieJar()))
    representative = build_opener(HTTPCookieProcessor(CookieJar()))
    admin_login = {"login": "test.admin", "password": environ["CABINET_TEST_PASSWORD"]}
    representative_login = {
        "login": "test.representative",
        "password": environ["CABINET_TEST_PASSWORD"],
    }

    with representative.open(BASE_URL + "/accounts", timeout=10) as login_page:
        assert login_page.status == 200
        assert login_page.geturl() == BASE_URL + "/login?from=accounts"

    status, _, headers = request(admin, "/api/auth/login", method="POST", body=admin_login, api=True)
    assert status == 200
    assert "httponly" in headers["Set-Cookie"].lower()
    expect_accounts(admin)

    status, body, _ = request(admin, "/api/roles", api=True)
    assert status == 200
    role_ids = {role["code"]: role["id"] for role in json.loads(body)}
    status, body, _ = request(
        admin,
        "/api/accounts",
        method="POST",
        body={**representative_login, "role_id": role_ids["representative"]},
        api=True,
    )
    assert status == 201
    account_id = json.loads(body)["id"]
    assert request(
        representative, "/api/auth/login", method="POST", body=representative_login, api=True
    )[0] == 200

    denied = request(representative, "/accounts")
    missing = request(representative, "/unknown-page")
    assert denied[0] == missing[0] == 404
    assert denied[1] == missing[1]
    assert denied[2]["Cache-Control"] == missing[2]["Cache-Control"] == "no-store"
    assert request(representative, "/api/roles", api=True)[0] == 404

    assert request(
        admin,
        f"/api/accounts/{account_id}/role",
        method="PATCH",
        body={"role_id": role_ids["admin"]},
        api=True,
    )[0] == 200
    expect_accounts(representative)
    assert request(representative, "/api/auth/logout", method="POST", api=True)[0] == 204
    assert request(representative, "/api/auth/me", api=True)[0] == 401
    with representative.open(BASE_URL + "/accounts", timeout=10) as login_page:
        assert login_page.geturl() == BASE_URL + "/login?from=accounts"
    print("Проверены статусы кабинета, смена роли и завершение сессии.")


if __name__ == "__main__":
    main()
