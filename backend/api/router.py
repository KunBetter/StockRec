from fastapi import APIRouter

from backend.api.endpoints import ai, auth, stocks, recommendations, market, analysis, profile, data

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(stocks.router, tags=["stocks"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(market.router, tags=["market"])
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(data.router, tags=["data"])
