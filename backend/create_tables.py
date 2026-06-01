from backend.database.database import Base, engine

from backend.models.product import Product
from backend.models.store import Store
from backend.models.store_product import StoreProduct
from backend.models.procurement_document import ProcurementDocument
from backend.models.price import Price
from backend.models.detected_anomaly import DetectedAnomaly
from backend.models.price_forecast import PriceForecast
from backend.models.correlation_analysis_result import CorrelationAnalysisResult
from backend.models.report import Report
from backend.models.market_factor import MarketFactor
from backend.models.category_factor_weight import CategoryFactorWeight
from backend.models.learned_factor_weight import LearnedFactorWeight


Base.metadata.create_all(bind=engine)

print("Таблицы успешно созданы")