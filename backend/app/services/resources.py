from app.schemas.resources import AgriculturalResource

AGRICULTURAL_RESOURCES = [
    AgriculturalResource(
        title="ICAR - Indian Council of Agricultural Research",
        category="research",
        url="https://icar.org.in",
        source="ICAR",
        description="Apex body for coordinating, guiding and managing research and education in agriculture in India.",
    ),
    AgriculturalResource(
        title="KVK Portal - Krishi Vigyan Kendras",
        category="advisory",
        url="https://kvk.icar.gov.in",
        source="ICAR",
        description="Network of agricultural extension centers providing technology assessment, refinement and demonstration.",
    ),
    AgriculturalResource(
        title="Farmer Portal - Government of India",
        category="schemes",
        url="https://farmer.gov.in",
        source="Ministry of Agriculture & Farmers Welfare",
        description="Unified portal for farmers to access schemes, advisories, and services.",
    ),
    AgriculturalResource(
        title="PM-KISAN - Pradhan Mantri Kisan Samman Nidhi",
        category="schemes",
        url="https://pmkisan.gov.in",
        source="Ministry of Agriculture & Farmers Welfare",
        description="Income support scheme providing Rs. 6000/year to eligible farmer families.",
    ),
    AgriculturalResource(
        title="PMFBY - Pradhan Mantri Fasal Bima Yojana",
        category="schemes",
        url="https://pmfby.gov.in",
        source="Ministry of Agriculture & Farmers Welfare",
        description="Crop insurance scheme providing financial support to farmers suffering crop loss/damage.",
    ),
    AgriculturalResource(
        title="Soil Health Card Scheme",
        category="advisory",
        url="https://soilhealth.dac.gov.in",
        source="Ministry of Agriculture & Farmers Welfare",
        description="Provides farmers with soil nutrient status and recommendations for improving soil fertility.",
    ),
    AgriculturalResource(
        title="eNAM - National Agriculture Market",
        category="market",
        url="https://enam.gov.in",
        source="Ministry of Agriculture & Farmers Welfare",
        description="Online trading platform for agricultural produce connecting markets across India.",
    ),
    AgriculturalResource(
        title="IMD - India Meteorological Department",
        category="weather",
        url="https://mausam.imd.gov.in",
        source="Ministry of Earth Sciences",
        description="Official weather forecasts, warnings, and agro-meteorological advisories for farmers.",
    ),
    AgriculturalResource(
        title="Kisan Call Center",
        category="advisory",
        url="https://kisan.gov.in",
        source="Ministry of Agriculture & Farmers Welfare",
        description="Toll-free helpline (1800-180-1551) for agricultural queries in multiple languages.",
    ),
    AgriculturalResource(
        title="AgriStack - Digital Agriculture Platform",
        category="digital",
        url="https://agristack.gov.in",
        source="Ministry of Agriculture & Farmers Welfare",
        description="Digital ecosystem for farmer databases, land records, and service delivery.",
    ),
    AgriculturalResource(
        title="NPCI - National Payments Corporation of India",
        category="financial",
        url="https://npci.org.in",
        source="NPCI",
        description="Digital payment systems including UPI, AePS for farmer financial inclusion.",
    ),
    AgriculturalResource(
        title="NABARD - National Bank for Agriculture and Rural Development",
        category="financial",
        url="https://nabard.org",
        source="NABARD",
        description="Apex development bank for agriculture and rural development credit and schemes.",
    ),
]


class ResourcesCatalogue:
    def __init__(self) -> None:
        self._resources = AGRICULTURAL_RESOURCES
        self._categories = self._extract_categories()

    def _extract_categories(self) -> list[str]:
        categories = set()
        for resource in self._resources:
            categories.add(resource.category)
        return sorted(categories)

    def get_all(self) -> list[AgriculturalResource]:
        return self._resources

    def get_by_category(self, category: str) -> list[AgriculturalResource]:
        return [r for r in self._resources if r.category.lower() == category.lower()]

    def get_categories(self) -> list[str]:
        return self._categories


resources_catalogue = ResourcesCatalogue()
