import decimal

import pydantic
import sanic
from sanic import exceptions

from src.entities import PaymentAccount, UserType
from src.handlers.utils import require, pydantic_response, Auth, PydanticJson, PydanticQuery
from src.services import billing
from src.services.auth import AuthResult

api_billing = sanic.Blueprint('api_billing', url_prefix='/billing')


class CreatePaymentAccountRequest(pydantic.BaseModel):
    user_id: int

class CreatePaymentAccountResponse(pydantic.BaseModel):
    payment_account: PaymentAccount

@api_billing.post('/payment_account/')
@require(
    auth=Auth(allowed=[UserType.admin, UserType.regular]),
    payload=PydanticJson(CreatePaymentAccountRequest),
)
async def create_payment_account(
        r: sanic.Request, auth: AuthResult, payload: CreatePaymentAccountRequest) -> sanic.HTTPResponse:
    billing_service: billing.BillingService = r.app.ctx.billing_service

    if auth.user_type is not UserType.admin and auth.user_id != payload.user_id:
        raise exceptions.Forbidden(f'Only user (id={auth.user_id}) data accessible.')

    try:
        payment_account = await billing_service.create_payment_account(payload.user_id)
    except billing.OwnerNotExist as e:
        raise exceptions.BadRequest(e)

    response = CreatePaymentAccountResponse(payment_account=payment_account)
    return pydantic_response(response)


class GetUserPaymentAccountsQuery(pydantic.BaseModel):
    user_id: int

class GetUserPaymentAccountsResponse(pydantic.BaseModel):
    payment_accounts: list[PaymentAccount]

@api_billing.get('/payment_accounts/')
@require(
    auth=Auth(allowed=[UserType.admin, UserType.regular]),
    query=PydanticQuery(GetUserPaymentAccountsQuery),
)
async def get_user_payment_accounts(
        r: sanic.Request, auth: AuthResult, query: GetUserPaymentAccountsQuery) -> sanic.HTTPResponse:
    billing_service: billing.BillingService = r.app.ctx.billing_service

    if auth.user_type is not UserType.admin and auth.user_id == query.user_id:
        raise exceptions.Forbidden(f'Only user (id={auth.user_id}) data accessible.')

    try:
        payment_accounts = await billing_service.get_payment_accounts(query.user_id)
    except billing.OwnerNotExist as e:
        raise exceptions.BadRequest(e)

    response = GetUserPaymentAccountsResponse(payment_accounts=payment_accounts)
    return pydantic_response(response)


class GetPaymentAccountResponse(pydantic.BaseModel):
    id: int
    user_id: int
    balance_rub: decimal.Decimal

@api_billing.get('/payment_account/<payment_account_id:int>/')
@require(
    auth=Auth(allowed=[UserType.admin, UserType.regular]),
)
async def get_payment_account(r: sanic.Request, payment_account_id: int, auth: AuthResult) -> sanic.HTTPResponse:
    billing_service: billing.BillingService = r.app.ctx.billing_service

    try:
        payment_account = await billing_service.get_payment_account(payment_account_id)
    except billing.PaymentAccountNotExist as e:
        raise exceptions.BadRequest(e)

    if auth.user_type is not UserType.admin and payment_account.user_id != auth.user_id:
        raise exceptions.Forbidden(f'Only user (id={auth.user_id}) data accessible.')

    response = GetPaymentAccountResponse(
        id=payment_account.id,
        user_id=payment_account.user_id,
        balance_rub=payment_account.balance_rub,
    )
    return pydantic_response(response)
