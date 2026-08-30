"""Saba Tours & Travels portfolio configuration from SRS (Aug 2026)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioWebsite:
    name: str
    domain: str
    base_url: str
    positioning: str
    seo_focus: str
    default_keywords: tuple[str, ...]


SABA_TOURS_PORTFOLIO: tuple[PortfolioWebsite, ...] = (
    PortfolioWebsite(
        name="One Way Drop",
        domain="onewaydrop.cab",
        base_url="https://onewaydrop.cab",
        positioning="One-way cab specialist",
        seo_focus="Pune–Mumbai one-way, airport and taxi keywords",
        default_keywords=(
            "pune to mumbai one way cab",
            "one way cab pune to mumbai",
            "pune mumbai one way taxi",
            "pune airport one way cab",
            "mumbai to pune one way cab",
        ),
    ),
    PortfolioWebsite(
        name="Saba Cabs",
        domain="sabacabs.com",
        base_url="https://sabacabs.com",
        positioning="Cab + airport + outstation",
        seo_focus="Pune–Mumbai, airport, EV and outstation keywords",
        default_keywords=(
            "pune to mumbai cab",
            "pune to mumbai innova cab",
            "pune airport cab booking",
            "outstation cab from pune",
            "ev cab pune mumbai",
        ),
    ),
    PortfolioWebsite(
        name="Pune Mumbai Cab Service",
        domain="punetomumbaicabservice.com",
        base_url="https://punetomumbaicabservice.com",
        positioning="Pune–Mumbai specialist",
        seo_focus="Route, booking, fare and airport keywords",
        default_keywords=(
            "pune to mumbai cab service",
            "pune mumbai cab fare",
            "pune to mumbai cab booking",
            "pune to mumbai airport cab",
            "mumbai to pune cab service",
        ),
    ),
)
