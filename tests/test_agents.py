"""
KENYABIZ AI
MULTI-AGENT TEST SUITE

Covers:
- Sales Agent
- Order Agent
- Support Agent
- Invoice Agent
- Payment Agent

Run:
    pytest tests\test_agents.py -v
"""

import pytest


# ============================================================
# IMPORT AGENTS
# ============================================================

import src.agents.sales_agent as sales_agent
import src.agents.order_agent as order_agent
import src.agents.support_agent as support_agent
import src.agents.invoice_agent as invoice_agent
import src.agents.payment_agent as payment_agent


# ============================================================
# TEST DATA
# ============================================================

OFFICE_CHAIR = {
    "product_id": "P001",
    "product_name": "Office Chair",
    "price_kes": 8500,
    "stock_quantity": 50,
}

OFFICE_DESK = {
    "product_id": "P002",
    "product_name": "Office Desk",
    "price_kes": 15000,
    "stock_quantity": 30,
}

MONITOR_STAND = {
    "product_id": "P007",
    "product_name": "Monitor Stand",
    "price_kes": 4500,
    "stock_quantity": 20,
}

SAMPLE_ORDER = {
    "order_reference": "KBA-20260925-P5EP",
    "customer_name": "Ambrose Lengerpei",
    "phone": "0712345678",
    "email": "ambrose@example.com",
    "status": "PENDING",
    "items": [
        {
            "product_id": "P001",
            "product_name": "Office Chair",
            "quantity": 2,
            "unit_price": 8500,
            "line_total": 17000,
        }
    ],
    "subtotal": 17000,
    "delivery_fee": 2500,
    "total": 19500,
    "currency": "KES",
}


# ################################################################
# SALES AGENT TESTS
# ################################################################


class TestSalesHelpers:
    """Tests for Sales Agent helper functions."""

    def test_normalize_text(self):
        result = sales_agent.normalize_text(
            "  OFFICE   CHAIR  "
        )

        assert result == "office chair"

    @pytest.mark.parametrize(
        "value,expected",
        [
            (8500, "KES 8,500.00"),
            (15000, "KES 15,000.00"),
            (0, "KES 0.00"),
            (12500.5, "KES 12,500.50"),
        ],
    )
    def test_format_currency(self, value, expected):
        assert sales_agent.format_currency(value) == expected

    def test_product_name_uses_product_name(self):
        assert (
            sales_agent.product_name(OFFICE_CHAIR)
            == "Office Chair"
        )

    def test_product_name_supports_name_field(self):
        product = {
            "product_id": "P001",
            "name": "Office Chair",
        }

        assert sales_agent.product_name(product) == "Office Chair"

    def test_product_price_uses_price_kes(self):
        assert sales_agent.product_price(
            OFFICE_CHAIR
        ) == 8500

    def test_product_price_supports_price_field(self):
        product = {
            "product_id": "P001",
            "price": 8500,
        }

        assert sales_agent.product_price(product) == 8500

    def test_product_stock_uses_stock_quantity(self):
        assert sales_agent.product_stock(
            OFFICE_CHAIR
        ) == 50

    def test_product_stock_supports_stock_field(self):
        product = {
            "product_id": "P001",
            "stock": 50,
        }

        assert sales_agent.product_stock(product) == 50


class TestSalesQuantityExtraction:
    """Tests quantity extraction."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("5 office chairs", 5),
            ("10 office desks", 10),
            ("2 monitors", 2),
            ("one office chair", 1),
            ("five office chairs", 5),
            ("twenty office chairs", 20),
            ("office chair", 1),
        ],
    )
    def test_extract_quantity(self, text, expected):
        assert (
            sales_agent.extract_quantity(text)
            == expected
        )

    def test_extract_quantity_zero_uses_default(self):
        assert (
            sales_agent.extract_quantity(
                "0 office chairs",
                default=1,
            )
            == 1
        )

    @pytest.mark.parametrize(
        "text,product,expected",
        [
            (
                "5 office chairs",
                "Office Chair",
                5,
            ),
            (
                "five office chairs",
                "Office Chair",
                5,
            ),
            (
                "5 office chairs and 2 office desks",
                "Office Chair",
                5,
            ),
            (
                "5 office chairs and 2 office desks",
                "Office Desk",
                2,
            ),
            (
                "office chair",
                "Office Chair",
                1,
            ),
        ],
    )
    def test_extract_quantity_for_product(
        self,
        text,
        product,
        expected,
    ):
        assert (
            sales_agent.extract_quantity_for_product(
                text,
                product,
            )
            == expected
        )


class TestSalesProductIdentification:
    """Tests product identification."""

    def test_identify_product_by_id(self, monkeypatch):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: (
                OFFICE_CHAIR
                if product_id == "P001"
                else None
            ),
        )

        result = sales_agent.identify_product(
            "How much is P001?"
        )

        assert result == OFFICE_CHAIR

    def test_identify_product_by_alias(self, monkeypatch):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: (
                OFFICE_CHAIR
                if product_id == "P001"
                else None
            ),
        )

        result = sales_agent.identify_product(
            "office chairs"
        )

        assert result["product_id"] == "P001"

    def test_identify_product_by_database_search(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: None,
        )

        monkeypatch.setattr(
            sales_agent,
            "search_products",
            lambda text: [MONITOR_STAND],
        )

        result = sales_agent.identify_product(
            "monitor stand"
        )

        assert result == MONITOR_STAND

    def test_identify_unknown_product(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: None,
        )

        monkeypatch.setattr(
            sales_agent,
            "search_products",
            lambda text: [],
        )

        result = sales_agent.identify_product(
            "smartphone"
        )

        assert result is None


class TestSalesCatalogue:
    """Tests product catalogue functions."""

    @pytest.mark.parametrize(
        "message",
        [
            "What products do you have?",
            "What products are available?",
            "What products do you sell?",
            "Show me your catalogue",
            "Show me all products",
            "List your products",
            "What items do you have?",
            "What do you sell?",
        ],
    )
    def test_catalogue_request_detection(
        self,
        message,
    ):
        assert (
            sales_agent.is_product_catalogue_request(
                message
            )
            is True
        )

    def test_non_catalogue_request(self):
        assert (
            sales_agent.is_product_catalogue_request(
                "How much is an office chair?"
            )
            is False
        )

    def test_format_product_catalogue(self):
        result = sales_agent.format_product_catalogue(
            [
                OFFICE_CHAIR,
                OFFICE_DESK,
            ]
        )

        assert "Office Chair" in result
        assert "Office Desk" in result
        assert "P001" in result
        assert "P002" in result
        assert "KES 8,500.00" in result
        assert "KES 15,000.00" in result

    def test_format_empty_catalogue(self):
        result = sales_agent.format_product_catalogue([])

        assert "no products" in result.lower()

    def test_get_product_catalogue(self, monkeypatch):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: {
                "P001": OFFICE_CHAIR,
                "P002": OFFICE_DESK,
            }.get(product_id),
        )

        result = sales_agent.get_product_catalogue()

        assert len(result) == 2
        assert result[0]["product_id"] == "P001"
        assert result[1]["product_id"] == "P002"


class TestSalesPrice:
    """Tests price requests."""

    def test_price_request_single_product(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "identify_product",
            lambda text: OFFICE_CHAIR,
        )

        result = sales_agent.process_price_request(
            "How much is an office chair?"
        )

        assert result["success"] is True
        assert result["type"] == "PRICE"
        assert result["quantity"] == 1
        assert result["unit_price"] == 8500
        assert result["total"] == 8500
        assert "KES 8,500.00" in result["response"]

    def test_price_request_multiple_units(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "identify_product",
            lambda text: OFFICE_CHAIR,
        )

        result = sales_agent.process_price_request(
            "How much are 5 office chairs?"
        )

        assert result["success"] is True
        assert result["quantity"] == 5
        assert result["total"] == 42500

    def test_price_request_unknown_product(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "identify_product",
            lambda text: None,
        )

        result = sales_agent.process_price_request(
            "How much is a smartphone?"
        )

        assert result["success"] is False
        assert result["type"] == "PRICE"
        assert "identify the product" in result["response"].lower()


class TestSalesStock:
    """Tests stock requests."""

    def test_stock_available(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "identify_product",
            lambda text: OFFICE_CHAIR,
        )

        monkeypatch.setattr(
            sales_agent,
            "check_stock",
            lambda product_id, quantity: {
                "available": True,
                "available_quantity": 50,
            },
        )

        result = sales_agent.process_stock_request(
            "Do you have 5 office chairs in stock?"
        )

        assert result["success"] is True
        assert result["type"] == "STOCK"
        assert result["available"] is True
        assert result["stock"] == 50

    def test_stock_insufficient(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "identify_product",
            lambda text: OFFICE_CHAIR,
        )

        monkeypatch.setattr(
            sales_agent,
            "check_stock",
            lambda product_id, quantity: {
                "available": False,
                "available_quantity": 2,
            },
        )

        result = sales_agent.process_stock_request(
            "Do you have 10 office chairs?"
        )

        assert result["success"] is True
        assert result["available"] is False
        assert result["stock"] == 2

    def test_stock_unknown_product(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "identify_product",
            lambda text: None,
        )

        result = sales_agent.process_stock_request(
            "Do you have smartphones?"
        )

        assert result["success"] is False
        assert result["type"] == "STOCK"


class TestSalesSearch:
    """Tests product search."""

    def test_product_search_success(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "search_products",
            lambda text: [
                OFFICE_CHAIR,
                OFFICE_DESK,
            ],
        )

        result = sales_agent.process_product_search(
            "office"
        )

        assert result["success"] is True
        assert result["type"] == "SEARCH"
        assert len(result["products"]) == 2
        assert "Office Chair" in result["response"]
        assert "Office Desk" in result["response"]

    def test_product_search_no_results(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "search_products",
            lambda text: [],
        )

        result = sales_agent.process_product_search(
            "smartphone"
        )

        assert result["success"] is False
        assert result["type"] == "SEARCH"
        assert "could not find" in result["response"].lower()


class TestSalesQuotation:
    """Tests quotation generation."""

    def test_extract_product_quantities(self):
        products = [
            OFFICE_CHAIR,
            OFFICE_DESK,
        ]

        result = (
            sales_agent.extract_product_quantities(
                "5 office chairs and 2 office desks",
                products,
            )
        )

        assert result == [
            {
                "product_id": "P001",
                "quantity": 5,
            },
            {
                "product_id": "P002",
                "quantity": 2,
            },
        ]

    def test_quotation_single_product(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: (
                OFFICE_CHAIR
                if product_id == "P001"
                else None
            ),
        )

        monkeypatch.setattr(
            sales_agent,
            "build_quotation",
            lambda items: {
                "items": [
                    {
                        "product_name": "Office Chair",
                        "quantity": 5,
                        "unit_price": 8500,
                        "line_total": 42500,
                    }
                ],
                "subtotal": 42500,
                "delivery_fee": 2500,
                "total": 45000,
            },
        )

        result = sales_agent.process_quotation_request(
            "Give me a quotation for 5 office chairs."
        )

        assert result["success"] is True
        assert result["type"] == "QUOTATION"
        assert result["subtotal"] == 42500
        assert result["delivery_fee"] == 2500
        assert result["total"] == 45000
        assert "Office Chair" in result["response"]

    def test_quotation_multiple_products(
        self,
        monkeypatch,
    ):
        def fake_get_product(product_id):
            return {
                "P001": OFFICE_CHAIR,
                "P002": OFFICE_DESK,
            }.get(product_id)

        monkeypatch.setattr(
            sales_agent,
            "get_product",
            fake_get_product,
        )

        monkeypatch.setattr(
            sales_agent,
            "build_quotation",
            lambda items: {
                "items": [
                    {
                        "product_name": "Office Chair",
                        "quantity": 5,
                        "unit_price": 8500,
                        "line_total": 42500,
                    },
                    {
                        "product_name": "Office Desk",
                        "quantity": 2,
                        "unit_price": 15000,
                        "line_total": 30000,
                    },
                ],
                "subtotal": 72500,
                "delivery_fee": 2500,
                "total": 75000,
            },
        )

        result = sales_agent.process_quotation_request(
            "Give me a quotation for 5 office chairs and 2 office desks."
        )

        assert result["success"] is True
        assert result["subtotal"] == 72500
        assert result["delivery_fee"] == 2500
        assert result["total"] == 75000
        assert len(result["items"]) == 2
        assert result["items"][0]["quantity"] == 5
        assert result["items"][1]["quantity"] == 2

    def test_quotation_unknown_product(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: None,
        )

        result = sales_agent.process_quotation_request(
            "Give me a quotation for a smartphone."
        )

        assert result["success"] is False
        assert result["type"] == "QUOTATION"
        assert "could not identify" in result["response"].lower()

    def test_quotation_tool_failure(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "get_product",
            lambda product_id: OFFICE_CHAIR,
        )

        monkeypatch.setattr(
            sales_agent,
            "build_quotation",
            lambda items: None,
        )

        result = sales_agent.process_quotation_request(
            "Give me a quotation for 2 office chairs."
        )

        assert result["success"] is False
        assert result["type"] == "QUOTATION"
        assert "could not generate" in result["response"].lower()


class TestSalesRecommendations:
    """Tests recommendation requests."""

    def test_recommendation_success(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "search_products",
            lambda text: [
                OFFICE_CHAIR,
                OFFICE_DESK,
            ],
        )

        result = sales_agent.process_recommendation_request(
            "Recommend office furniture"
        )

        assert result["success"] is True
        assert result["type"] == "RECOMMENDATION"
        assert len(result["products"]) == 2
        assert "Office Chair" in result["response"]

    def test_recommendation_falls_back_to_catalogue(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "search_products",
            lambda text: [],
        )

        monkeypatch.setattr(
            sales_agent,
            "get_product_catalogue",
            lambda: [
                OFFICE_CHAIR,
                OFFICE_DESK,
            ],
        )

        result = sales_agent.process_recommendation_request(
            "Recommend something"
        )

        assert result["success"] is True
        assert len(result["products"]) == 2

    def test_recommendation_no_products(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            sales_agent,
            "search_products",
            lambda text: [],
        )

        monkeypatch.setattr(
            sales_agent,
            "get_product_catalogue",
            lambda: [],
        )

        result = sales_agent.process_recommendation_request(
            "Recommend something"
        )

        assert result["success"] is False
        assert result["type"] == "RECOMMENDATION"


class TestSalesClassification:
    """Tests sales request classification."""

    @pytest.mark.parametrize(
        "message,expected",
        [
            ("What products do you have?", "CATALOGUE"),
            ("Show me all products", "CATALOGUE"),
            ("Give me a quotation", "QUOTATION"),
            ("Give me a quote", "QUOTATION"),
            ("Is the office chair in stock?", "STOCK"),
            ("Do you have office desks?", "STOCK"),
            ("Recommend an office chair", "RECOMMENDATION"),
            ("Which product is best?", "RECOMMENDATION"),
            ("How much is an office chair?", "PRICE"),
            ("What is the price of P001?", "PRICE"),
            ("Find office furniture", "SEARCH"),
            ("Search for chairs", "SEARCH"),
        ],
    )
    def test_classify_sales_request(
        self,
        message,
        expected,
    ):
        assert (
            sales_agent.classify_sales_request(message)
            == expected
        )


class TestSalesMainProcessor:
    """Tests main sales processor."""

    def test_empty_sales_request(self):
        result = sales_agent.process_sales_request("")

        assert result["success"] is False
        assert result["type"] == "UNKNOWN"

    def test_none_sales_request(self):
        result = sales_agent.process_sales_request(None)

        assert result["success"] is False
        assert result["type"] == "UNKNOWN"

    def test_catalogue_routing(
        self,
        monkeypatch,
    ):
        expected = {
            "success": True,
            "type": "CATALOGUE",
            "response": "catalogue",
        }

        monkeypatch.setattr(
            sales_agent,
            "process_product_catalogue_request",
            lambda: expected,
        )

        result = sales_agent.process_sales_request(
            "What products do you have?"
        )

        assert result == expected

    def test_price_routing(
        self,
        monkeypatch,
    ):
        expected = {
            "success": True,
            "type": "PRICE",
            "response": "price",
        }

        monkeypatch.setattr(
            sales_agent,
            "process_price_request",
            lambda text: expected,
        )

        result = sales_agent.process_sales_request(
            "How much is an office chair?"
        )

        assert result == expected

    def test_stock_routing(
        self,
        monkeypatch,
    ):
        expected = {
            "success": True,
            "type": "STOCK",
            "response": "stock",
        }

        monkeypatch.setattr(
            sales_agent,
            "process_stock_request",
            lambda text: expected,
        )

        result = sales_agent.process_sales_request(
            "Is an office chair in stock?"
        )

        assert result == expected

    def test_search_routing(
        self,
        monkeypatch,
    ):
        expected = {
            "success": True,
            "type": "SEARCH",
            "response": "search",
        }

        monkeypatch.setattr(
            sales_agent,
            "process_product_search",
            lambda text: expected,
        )

        result = sales_agent.process_sales_request(
            "Find office chairs"
        )

        assert result == expected


# ################################################################
# ORDER AGENT TESTS
# ################################################################


class TestOrderHelpers:
    """Tests order-agent helper functions."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Office Chair", "office chair"),
            ("office chairs", "office chair"),
            ("Office Chairs!", "office chair"),
            ("OFFICE DESKS", "office desk"),

            # Current order_agent.py does not normalize
            # the irregular plural "mice".
            ("wireless mice", "wireless mice"),

            ("laptops", "laptop"),
        ],
    )
    def test_normalize_product_name(
        self,
        value,
        expected,
    ):
        assert (
            order_agent.normalize_product_name(value)
            == expected
        )


class TestOrderProductMatching:
    """Tests product matching."""

    def test_find_product_matches_exact(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "search_products",
            lambda text: [OFFICE_CHAIR],
        )

        result = order_agent.find_product_matches(
            "office chair"
        )

        assert len(result) == 1
        assert result[0]["product_id"] == "P001"

    def test_find_product_matches_plural(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "search_products",
            lambda text: [OFFICE_CHAIR],
        )

        result = order_agent.find_product_matches(
            "office chairs"
        )

        assert len(result) == 1
        assert result[0]["product_id"] == "P001"

    def test_find_product_matches_removes_duplicates(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "search_products",
            lambda text: [
                OFFICE_CHAIR,
                OFFICE_CHAIR,
            ],
        )

        result = order_agent.find_product_matches(
            "office chair"
        )

        assert len(result) == 1

    def test_find_product_not_found(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "search_products",
            lambda text: [],
        )

        result = order_agent.find_product(
            "smartphone"
        )

        assert result["status"] == "NOT_FOUND"

    def test_find_product_found(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "search_products",
            lambda text: [OFFICE_CHAIR],
        )

        result = order_agent.find_product(
            "office chair"
        )

        assert result["status"] == "FOUND"
        assert result["product"]["product_id"] == "P001"

    def test_find_product_ambiguous(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "search_products",
            lambda text: [
                OFFICE_CHAIR,
                OFFICE_DESK,
            ],
        )

        result = order_agent.find_product(
            "office"
        )

        assert result["status"] in {
            "FOUND",
            "AMBIGUOUS",
        }


class TestOrderValidation:
    """Tests order item validation."""

    def test_validate_order_items_empty(self):
        result = order_agent.validate_order_items([])

        assert result["status"] == "ERROR"

    def test_validate_order_items_zero_quantity(
        self,
    ):
        items = [
            order_agent.OrderItem(
                product_name="office chair",
                quantity=0,
            )
        ]

        result = order_agent.validate_order_items(
            items
        )

        assert result["status"] == "ERROR"

    def test_validate_order_items_negative_quantity(
        self,
    ):
        items = [
            order_agent.OrderItem(
                product_name="office chair",
                quantity=-1,
            )
        ]

        result = order_agent.validate_order_items(
            items
        )

        assert result["status"] == "ERROR"

    def test_validate_order_items_product_not_found(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "find_product",
            lambda name: {
                "status": "NOT_FOUND",
            },
        )

        items = [
            order_agent.OrderItem(
                product_name="smartphone",
                quantity=1,
            )
        ]

        result = order_agent.validate_order_items(
            items
        )

        assert result["status"] == "PRODUCT_NOT_FOUND"

    def test_validate_order_items_ambiguous(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "find_product",
            lambda name: {
                "status": "AMBIGUOUS",
                "matches": [
                    OFFICE_CHAIR,
                    OFFICE_DESK,
                ],
            },
        )

        items = [
            order_agent.OrderItem(
                product_name="office",
                quantity=1,
            )
        ]

        result = order_agent.validate_order_items(
            items
        )

        assert result["status"] == "AMBIGUOUS_PRODUCT"

    def test_validate_order_items_insufficient_stock(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "find_product",
            lambda name: {
                "status": "FOUND",
                "product": OFFICE_CHAIR,
            },
        )

        # validate_order_items() treats a falsy check_stock()
        # result as insufficient stock.
        monkeypatch.setattr(
            order_agent,
            "check_stock",
            lambda product_id, quantity: False,
        )

        items = [
            order_agent.OrderItem(
                product_name="office chair",
                quantity=9999,
            )
        ]

        result = order_agent.validate_order_items(
            items
        )

        assert result["status"] == "INSUFFICIENT_STOCK"

    def test_validate_order_items_success(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "find_product",
            lambda name: {
                "status": "FOUND",
                "product": OFFICE_CHAIR,
            },
        )

        monkeypatch.setattr(
            order_agent,
            "check_stock",
            lambda product_id, quantity: {
                "available": True,
                "available_quantity": 50,
            },
        )

        items = [
            order_agent.OrderItem(
                product_name="office chair",
                quantity=2,
            )
        ]

        result = order_agent.validate_order_items(
            items
        )

        assert result["status"] == "SUCCESS"
        assert result["items"][0]["product_id"] == "P001"
        assert result["items"][0]["quantity"] == 2


class TestOrderProcessing:
    """Tests order processing."""

    def test_process_order_missing_message(self):
        result = order_agent.process_order(
            None,
            confirmed=True,
        )

        assert result["status"] == "ERROR"

    def test_process_order_requires_confirmation(
        self,
    ):
        result = order_agent.process_order(
            "I want 2 office chairs",
            confirmed=False,
        )

        assert result["status"] == "AWAITING_CONFIRMATION"

    def test_process_order_customer_details_required(
        self,
        monkeypatch,
    ):
        customer = order_agent.CustomerInformation(
            name="",
            phone=None,
            email=None,
        )

        request = order_agent.OrderRequest(
            customer=customer,
            items=[
                order_agent.OrderItem(
                    product_name="office chair",
                    quantity=2,
                )
            ],
        )

        monkeypatch.setattr(
            order_agent,
            "extract_order_information",
            lambda message: request,
        )

        result = order_agent.process_order(
            "I want 2 office chairs",
            confirmed=True,
        )

        assert result["status"] == "CUSTOMER_DETAILS_REQUIRED"

    def test_process_order_validation_failure(
        self,
        monkeypatch,
    ):
        customer = order_agent.CustomerInformation(
            name="Ambrose Lengerpei",
            phone="0712345678",
            email=None,
        )

        request = order_agent.OrderRequest(
            customer=customer,
            items=[
                order_agent.OrderItem(
                    product_name="smartphone",
                    quantity=1,
                )
            ],
        )

        monkeypatch.setattr(
            order_agent,
            "extract_order_information",
            lambda message: request,
        )

        monkeypatch.setattr(
            order_agent,
            "validate_order_items",
            lambda items: {
                "status": "PRODUCT_NOT_FOUND",
                "message": "Product not found.",
            },
        )

        result = order_agent.process_order(
            "I want a smartphone",
            confirmed=True,
        )

        assert result["status"] == "PRODUCT_NOT_FOUND"

    def test_process_order_success(
        self,
        monkeypatch,
    ):
        customer = order_agent.CustomerInformation(
            name="Ambrose Lengerpei",
            phone="0712345678",
            email="ambrose@example.com",
        )

        request = order_agent.OrderRequest(
            customer=customer,
            items=[
                order_agent.OrderItem(
                    product_name="office chair",
                    quantity=2,
                )
            ],
        )

        monkeypatch.setattr(
            order_agent,
            "extract_order_information",
            lambda message: request,
        )

        monkeypatch.setattr(
            order_agent,
            "validate_order_items",
            lambda items: {
                "status": "SUCCESS",
                "items": [
                    {
                        "product_id": "P001",
                        "quantity": 2,
                    }
                ],
            },
        )

        monkeypatch.setattr(
            order_agent,
            "create_order",
            lambda **kwargs: {
                "status": "SUCCESS",
                "order_reference": "KBA-TEST-0001",
                "customer_name": "Ambrose Lengerpei",
                "items": [
                    {
                        "product_id": "P001",
                        "quantity": 2,
                    }
                ],
                "subtotal": 17000,
                "delivery_fee": 2500,
                "total": 19500,
            },
        )

        result = order_agent.process_order(
            "I want 2 office chairs",
            confirmed=True,
        )

        assert result["status"] == "SUCCESS"
        assert (
            result["order"]["order_reference"]
            == "KBA-TEST-0001"
        )


class TestOrderFormatting:
    """Tests order response formatting."""

    def test_format_awaiting_confirmation(self):
        result = {
            "status": "AWAITING_CONFIRMATION",
            "message": "Please confirm the order.",
        }

        response = order_agent.format_order_response(
            result
        )

        assert "confirm" in response.lower()

    def test_format_customer_details_required(self):
        result = {
            "status": "CUSTOMER_DETAILS_REQUIRED",
            "message": "Customer name is required.",
        }

        response = order_agent.format_order_response(
            result
        )

        assert "customer" in response.lower()

    def test_format_product_not_found(self):
        result = {
            "status": "PRODUCT_NOT_FOUND",
            "message": "Product was not found.",
        }

        response = order_agent.format_order_response(
            result
        )

        assert "product" in response.lower()

    def test_format_insufficient_stock(self):
        result = {
            "status": "INSUFFICIENT_STOCK",
            "message": "Not enough stock.",
        }

        response = order_agent.format_order_response(
            result
        )

        assert "stock" in response.lower()

    def test_format_success(self):
        result = {
            "status": "SUCCESS",
            "order": SAMPLE_ORDER,
        }

        response = order_agent.format_order_response(
            result
        )

        assert "KBA-20260925-P5EP" in response
        assert "Ambrose Lengerpei" in response

    def test_lookup_order_missing_reference(self):
        result = order_agent.lookup_order(None)

        assert result["status"] == "ERROR"

    def test_lookup_order_not_found(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "get_order",
            lambda reference: None,
        )

        result = order_agent.lookup_order(
            "KBA-UNKNOWN"
        )

        assert result["status"] == "NOT_FOUND"

    def test_lookup_order_success(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            order_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        result = order_agent.lookup_order(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "SUCCESS"
        assert (
            result["order"]["order_reference"]
            == "KBA-20260925-P5EP"
        )

    def test_format_existing_order(self):
        result = {
            "status": "SUCCESS",
            "order": SAMPLE_ORDER,
        }

        response = order_agent.format_existing_order(
            result
        )

        assert "KBA-20260925-P5EP" in response
        assert "Office Chair" in response


# ################################################################
# SUPPORT AGENT TESTS
# ################################################################


class TestSupportAgent:
    """Tests Support Agent."""

    def test_missing_question_none(self):
        result = support_agent.answer_customer_question(
            None
        )

        assert "provide a question" in result.lower()

    def test_missing_question_empty(self):
        result = support_agent.answer_customer_question(
            ""
        )

        assert "provide a question" in result.lower()

    def test_whitespace_question(self):
        result = support_agent.answer_customer_question(
            "   "
        )

        assert isinstance(result, str)
        assert "could not find enough information" in result.lower()

    def test_no_context(self, monkeypatch):
        monkeypatch.setattr(
            support_agent,
            "retrieve_documents",
            lambda question, top_k=2: [],
        )

        monkeypatch.setattr(
            support_agent,
            "format_context",
            lambda documents: "",
        )

        result = support_agent.answer_customer_question(
            "What is your delivery policy?"
        )

        assert "could not find enough information" in result.lower()

    def test_successful_answer(self, monkeypatch):
        documents = [
            {
                "source": "faq.md",
                "content": "KenyaBiz provides delivery services.",
            }
        ]

        monkeypatch.setattr(
            support_agent,
            "format_context",
            lambda docs: "KenyaBiz provides delivery services.",
        )

        class FakeResponse:
            content = "KenyaBiz provides delivery services."

        class FakeLLM:
            def invoke(self, prompt):
                return FakeResponse()

        monkeypatch.setattr(
            support_agent,
            "llm",
            FakeLLM(),
        )

        result = support_agent.answer_customer_question(
            "Do you provide delivery?",
            retrieved_documents=documents,
        )

        assert result == (
            "KenyaBiz provides delivery services."
        )

    def test_llm_error(self, monkeypatch):
        monkeypatch.setattr(
            support_agent,
            "format_context",
            lambda docs: "Some useful context.",
        )

        class FakeLLM:
            def invoke(self, prompt):
                raise RuntimeError("LLM failure")

        monkeypatch.setattr(
            support_agent,
            "llm",
            FakeLLM(),
        )

        result = support_agent.answer_customer_question(
            "What services do you provide?",
            retrieved_documents=[
                {
                    "source": "faq.md",
                    "content": "Services",
                }
            ],
        )

        assert "encountered an error" in result.lower()

    def test_get_support_response_missing_question(
        self,
    ):
        result = support_agent.get_support_response(
            None
        )

        assert result["question"] == ""
        assert result["sources"] == []
        assert "provide a question" in result["answer"].lower()

    def test_get_support_response(
        self,
        monkeypatch,
    ):
        documents = [
            {
                "source": "faq.md",
                "content": "Frequently asked questions.",
            }
        ]

        monkeypatch.setattr(
            support_agent,
            "retrieve_documents",
            lambda question, top_k=2: documents,
        )

        monkeypatch.setattr(
            support_agent,
            "format_context",
            lambda docs: "Frequently asked questions.",
        )

        class FakeResponse:
            content = "This is the answer."

        class FakeLLM:
            def invoke(self, prompt):
                return FakeResponse()

        monkeypatch.setattr(
            support_agent,
            "llm",
            FakeLLM(),
        )

        result = support_agent.get_support_response(
            "What is your policy?"
        )

        assert result["question"] == "What is your policy?"
        assert result["answer"] == "This is the answer."
        assert result["sources"] == ["faq.md"]


# ################################################################
# INVOICE AGENT TESTS
# ################################################################


class TestInvoiceAgent:
    """Tests Invoice Agent."""

    def test_missing_order_reference_none(self):
        result = invoice_agent.process_invoice_request(
            None
        )

        assert result["status"] == "ERROR"
        assert "order reference" in result["message"].lower()

    def test_missing_order_reference_empty(self):
        result = invoice_agent.process_invoice_request(
            ""
        )

        assert result["status"] == "ERROR"
        assert "order reference" in result["message"].lower()

    def test_whitespace_order_reference(self):
        result = invoice_agent.process_invoice_request(
            "   "
        )

        assert result["status"] == "NOT_FOUND"

    def test_order_not_found(self, monkeypatch):
        monkeypatch.setattr(
            invoice_agent,
            "get_order",
            lambda reference: None,
        )

        result = invoice_agent.process_invoice_request(
            "KBA-UNKNOWN"
        )

        assert result["status"] == "NOT_FOUND"

    def test_invoice_tool_error(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            invoice_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            invoice_agent,
            "generate_invoice",
            lambda reference: {
                "status": "ERROR",
                "message": "Invoice generation failed.",
            },
        )

        result = invoice_agent.process_invoice_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "ERROR"
        assert "invoice generation failed" in result["message"].lower()

    def test_invoice_success_dict_response(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            invoice_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            invoice_agent,
            "generate_invoice",
            lambda reference: {
                "status": "SUCCESS",
                "invoice_path": "invoices/test.pdf",
            },
        )

        result = invoice_agent.process_invoice_request(
            "kba-20260925-p5ep"
        )

        assert result["status"] == "SUCCESS"
        assert result["order_reference"] == (
            "KBA-20260925-P5EP"
        )
        assert result["invoice_path"] == (
            "invoices/test.pdf"
        )

    def test_invoice_success_string_response(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            invoice_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            invoice_agent,
            "generate_invoice",
            lambda reference: "invoices/test.pdf",
        )

        result = invoice_agent.process_invoice_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "SUCCESS"
        assert result["invoice_path"] == (
            "invoices/test.pdf"
        )

    def test_invoice_missing_file_path(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            invoice_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            invoice_agent,
            "generate_invoice",
            lambda reference: {
                "status": "SUCCESS",
            },
        )

        result = invoice_agent.process_invoice_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "ERROR"

    def test_format_invoice_not_found(self):
        result = {
            "status": "NOT_FOUND",
            "message": "Order not found.",
        }

        response = invoice_agent.format_invoice_response(
            result
        )

        assert response == "Order not found."

    def test_format_invoice_error(self):
        result = {
            "status": "ERROR",
            "message": "Unable to generate invoice.",
        }

        response = invoice_agent.format_invoice_response(
            result
        )

        assert "could not generate" in response.lower()

    def test_format_invoice_success(self):
        result = {
            "status": "SUCCESS",
            "order_reference": "KBA-20260925-P5EP",
            "invoice_path": "invoices/test.pdf",
            "order": SAMPLE_ORDER,
        }

        response = invoice_agent.format_invoice_response(
            result
        )

        assert "Invoice generated successfully" in response
        assert "KBA-20260925-P5EP" in response
        assert "Ambrose Lengerpei" in response
        assert "Office Chair" in response
        assert "KES 19,500.00" in response
        assert "invoices/test.pdf" in response


# ################################################################
# PAYMENT AGENT TESTS
# ################################################################


class TestPaymentAgentRequest:
    """Tests payment request creation."""

    def test_missing_order_reference_none(self):
        result = payment_agent.process_payment_request(
            None
        )

        assert result["status"] == "ERROR"
        assert "order reference" in result["message"].lower()

    def test_missing_order_reference_empty(self):
        result = payment_agent.process_payment_request(
            ""
        )

        assert result["status"] == "ERROR"
        assert "order reference" in result["message"].lower()

    def test_whitespace_order_reference(self):
        result = payment_agent.process_payment_request(
            "   "
        )

        assert result["status"] == "NOT_FOUND"

    def test_order_not_found(self, monkeypatch):
        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: None,
        )

        result = payment_agent.process_payment_request(
            "KBA-UNKNOWN"
        )

        assert result["status"] == "NOT_FOUND"

    def test_existing_paid_payment(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            payment_agent,
            "get_order_payments",
            lambda reference: {
                "status": "SUCCESS",
                "payments": [
                    {
                        "payment_reference": "MPS123",
                        "status": "PAID",
                        "amount": 19500,
                    }
                ],
            },
        )

        result = payment_agent.process_payment_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "ALREADY_PAID"
        assert result["payment_reference"] == "MPS123"

    def test_existing_pending_payment(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            payment_agent,
            "get_order_payments",
            lambda reference: {
                "status": "SUCCESS",
                "payments": [
                    {
                        "payment_reference": "MPS123",
                        "status": "PENDING",
                        "amount": 19500,
                        "method": "M-PESA-SIMULATION",
                    }
                ],
            },
        )

        result = payment_agent.process_payment_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == (
            "PAYMENT_ALREADY_PENDING"
        )
        assert result["payment_reference"] == "MPS123"

    def test_inconsistent_paid_order(
        self,
        monkeypatch,
    ):
        paid_order = {
            **SAMPLE_ORDER,
            "status": "PAID",
        }

        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: paid_order,
        )

        monkeypatch.setattr(
            payment_agent,
            "get_order_payments",
            lambda reference: {
                "status": "SUCCESS",
                "payments": [],
            },
        )

        result = payment_agent.process_payment_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == (
            "PAYMENT_STATE_INCONSISTENT"
        )

    def test_order_missing_total(
        self,
        monkeypatch,
    ):
        order = {
            **SAMPLE_ORDER,
        }
        order.pop("total")

        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: order,
        )

        monkeypatch.setattr(
            payment_agent,
            "get_order_payments",
            lambda reference: {
                "status": "SUCCESS",
                "payments": [],
            },
        )

        result = payment_agent.process_payment_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "ERROR"
        assert "total" in result["message"].lower()

    def test_payment_request_success(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            payment_agent,
            "get_order_payments",
            lambda reference: {
                "status": "SUCCESS",
                "payments": [],
            },
        )

        monkeypatch.setattr(
            payment_agent,
            "create_payment_request",
            lambda reference: {
                "status": "SUCCESS",
                "payment_reference": "MPS12345",
                "amount": 19500,
                "payment_status": "PENDING",
                "method": "M-PESA-SIMULATION",
            },
        )

        result = payment_agent.process_payment_request(
            "kba-20260925-p5ep"
        )

        assert result["status"] == (
            "PAYMENT_REQUEST_CREATED"
        )
        assert result["order_reference"] == (
            "KBA-20260925-P5EP"
        )
        assert result["payment_reference"] == "MPS12345"
        assert result["amount"] == 19500
        assert result["currency"] == "KES"
        assert result["payment_status"] == "PENDING"

    def test_payment_tool_returns_error(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            payment_agent,
            "get_order_payments",
            lambda reference: {
                "status": "SUCCESS",
                "payments": [],
            },
        )

        monkeypatch.setattr(
            payment_agent,
            "create_payment_request",
            lambda reference: {
                "status": "ERROR",
                "message": "Payment tool failed.",
            },
        )

        result = payment_agent.process_payment_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "ERROR"
        assert "payment tool failed" in result["message"].lower()

    def test_payment_tool_returns_empty(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_order",
            lambda reference: SAMPLE_ORDER,
        )

        monkeypatch.setattr(
            payment_agent,
            "get_order_payments",
            lambda reference: {
                "status": "SUCCESS",
                "payments": [],
            },
        )

        monkeypatch.setattr(
            payment_agent,
            "create_payment_request",
            lambda reference: None,
        )

        result = payment_agent.process_payment_request(
            "KBA-20260925-P5EP"
        )

        assert result["status"] == "ERROR"


# ################################################################
# PAYMENT COMPLETION TESTS
# ################################################################


class TestPaymentCompletion:
    """Tests payment completion."""

    def test_missing_payment_reference_none(self):
        result = payment_agent.process_payment_completion(
            None
        )

        assert result["status"] == "ERROR"
        assert "payment reference" in result["message"].lower()

    def test_missing_payment_reference_empty(self):
        result = payment_agent.process_payment_completion(
            ""
        )

        assert result["status"] == "ERROR"
        assert "payment reference" in result["message"].lower()

    def test_whitespace_payment_reference(self):
        result = payment_agent.process_payment_completion(
            "   "
        )

        assert result["status"] == "ERROR"
        assert "payment" in result["message"].lower()

    def test_already_paid_payment(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: {
                "status": "SUCCESS",
                "payment": {
                    "payment_reference": "MPS123",
                    "payment_status": "PAID",
                    "amount": 19500,
                },
            },
        )

        result = payment_agent.process_payment_completion(
            "mps123"
        )

        assert result["status"] == "ALREADY_PAID"
        assert result["payment_reference"] == "MPS123"

    def test_payment_completion_empty_result(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: {
                "status": "NOT_FOUND",
            },
        )

        monkeypatch.setattr(
            payment_agent,
            "complete_payment",
            lambda reference: None,
        )

        result = payment_agent.process_payment_completion(
            "MPS123"
        )

        assert result["status"] == "ERROR"

    def test_payment_completion_tool_error(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: {
                "status": "NOT_FOUND",
            },
        )

        monkeypatch.setattr(
            payment_agent,
            "complete_payment",
            lambda reference: {
                "status": "ERROR",
                "message": "Payment completion failed.",
            },
        )

        result = payment_agent.process_payment_completion(
            "MPS123"
        )

        assert result["status"] == "ERROR"
        assert "completion failed" in result["message"].lower()

    def test_payment_completion_success_dict(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: {
                "status": "NOT_FOUND",
            },
        )

        monkeypatch.setattr(
            payment_agent,
            "complete_payment",
            lambda reference: {
                "payment_reference": "MPS123",
                "payment_status": "PAID",
                "amount": 19500,
            },
        )

        result = payment_agent.process_payment_completion(
            "mps123"
        )

        assert result["status"] == "PAYMENT_COMPLETED"
        assert result["payment_reference"] == "MPS123"
        assert result["payment"]["payment_status"] == "PAID"

    def test_payment_completion_success_non_dict(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: {
                "status": "NOT_FOUND",
            },
        )

        monkeypatch.setattr(
            payment_agent,
            "complete_payment",
            lambda reference: "MPS123",
        )

        result = payment_agent.process_payment_completion(
            "mps123"
        )

        assert result["status"] == "PAYMENT_COMPLETED"


# ################################################################
# PAYMENT STATUS TESTS
# ################################################################


class TestPaymentStatus:
    """Tests payment status."""

    def test_missing_payment_reference_none(self):
        result = payment_agent.check_payment_status(
            None
        )

        assert result["status"] == "ERROR"
        assert "payment reference" in result["message"].lower()

    def test_missing_payment_reference_empty(self):
        result = payment_agent.check_payment_status(
            ""
        )

        assert result["status"] == "ERROR"
        assert "payment reference" in result["message"].lower()

    def test_whitespace_payment_reference(self):
        result = payment_agent.check_payment_status(
            "   "
        )

        assert result["status"] == "NOT_FOUND"

    def test_payment_not_found(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: None,
        )

        result = payment_agent.check_payment_status(
            "MPS-UNKNOWN"
        )

        assert result["status"] == "NOT_FOUND"

    def test_payment_status_tool_error(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: {
                "status": "ERROR",
                "message": "Payment not found.",
            },
        )

        result = payment_agent.check_payment_status(
            "MPS-UNKNOWN"
        )

        assert result["status"] == "NOT_FOUND"

    def test_payment_status_success(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            payment_agent,
            "get_payment_status",
            lambda reference: {
                "status": "SUCCESS",
                "payment": {
                    "payment_reference": "MPS123",
                    "payment_status": "PENDING",
                    "amount": 19500,
                    "order_reference": "KBA-20260925-P5EP",
                    "method": "M-PESA-SIMULATION",
                },
            },
        )

        result = payment_agent.check_payment_status(
            "mps123"
        )

        assert result["status"] == "SUCCESS"
        assert result["payment_reference"] == "MPS123"


# ################################################################
# PAYMENT FORMATTING TESTS
# ################################################################


class TestPaymentFormatting:
    """Tests payment response formatting."""

    def test_format_payment_request_not_found(self):
        result = {
            "status": "NOT_FOUND",
            "message": "Order not found.",
        }

        response = payment_agent.format_payment_request(
            result
        )

        assert response == "Order not found."

    def test_format_payment_request_already_paid(self):
        result = {
            "status": "ALREADY_PAID",
            "message": "Order already paid.",
            "payment_reference": "MPS123",
            "amount": 19500,
        }

        response = payment_agent.format_payment_request(
            result
        )

        assert "already paid" in response.lower()
        assert "MPS123" in response
        assert "19,500.00" in response

    def test_format_payment_request_pending(self):
        result = {
            "status": "PAYMENT_ALREADY_PENDING",
            "order_reference": "KBA-20260925-P5EP",
            "payment_reference": "MPS123",
            "amount": 19500,
            "currency": "KES",
            "payment_method": "M-PESA-SIMULATION",
        }

        response = payment_agent.format_payment_request(
            result
        )

        assert "already exists" in response.lower()
        assert "KBA-20260925-P5EP" in response
        assert "MPS123" in response
        assert "PENDING" in response

    def test_format_payment_request_inconsistent(self):
        result = {
            "status": "PAYMENT_STATE_INCONSISTENT",
            "message": "Payment state is inconsistent.",
        }

        response = payment_agent.format_payment_request(
            result
        )

        assert response == (
            "Payment state is inconsistent."
        )

    def test_format_payment_request_error(self):
        result = {
            "status": "ERROR",
            "message": "Payment failed.",
        }

        response = payment_agent.format_payment_request(
            result
        )

        assert "could not create" in response.lower()
        assert "payment failed" in response.lower()

    def test_format_payment_request_success(self):
        result = {
            "status": "PAYMENT_REQUEST_CREATED",
            "order_reference": "KBA-20260925-P5EP",
            "payment_reference": "MPS123",
            "amount": 19500,
            "currency": "KES",
            "payment_method": "M-PESA-SIMULATION",
            "payment_status": "PENDING",
        }

        response = payment_agent.format_payment_request(
            result
        )

        assert "Payment request created successfully" in response
        assert "KBA-20260925-P5EP" in response
        assert "MPS123" in response
        assert "KES 19,500.00" in response
        assert "PENDING" in response
        assert "simulated" in response.lower()

    def test_format_payment_completion_already_paid(self):
        result = {
            "status": "ALREADY_PAID",
            "message": "Payment already completed.",
        }

        response = payment_agent.format_payment_completion(
            result
        )

        assert response == "Payment already completed."

    def test_format_payment_completion_error(self):
        result = {
            "status": "ERROR",
            "message": "Unable to complete payment.",
        }

        response = payment_agent.format_payment_completion(
            result
        )

        assert "could not complete" in response.lower()

    def test_format_payment_completion_success(self):
        result = {
            "status": "PAYMENT_COMPLETED",
            "payment_reference": "MPS123",
        }

        response = payment_agent.format_payment_completion(
            result
        )

        assert "completed successfully" in response.lower()
        assert "MPS123" in response
        assert "PAID" in response

    def test_format_payment_status_error(self):
        result = {
            "status": "NOT_FOUND",
            "message": "Payment not found.",
        }

        response = payment_agent.format_payment_status(
            result
        )

        assert response == "Payment not found."

    def test_format_payment_status_success_dict(self):
        result = {
            "status": "SUCCESS",
            "payment_reference": "MPS123",
            "payment": {
                "payment_status": "PENDING",
                "order_reference": "KBA-20260925-P5EP",
                "amount": 19500,
                "method": "M-PESA-SIMULATION",
            },
        }

        response = payment_agent.format_payment_status(
            result
        )

        assert "Payment status" in response
        assert "MPS123" in response
        assert "PENDING" in response
        assert "KBA-20260925-P5EP" in response
        assert "19,500.00" in response

    def test_format_payment_status_non_dict(self):
        result = {
            "status": "SUCCESS",
            "payment_reference": "MPS123",
            "payment": "PAID",
        }

        response = payment_agent.format_payment_status(
            result
        )

        assert "MPS123" in response
        assert "PAID" in response


# ################################################################
# CROSS-AGENT BASIC TESTS
# ################################################################


class TestAgentIntegrationBasics:
    """
    Basic checks that the expected agent entry points
    are available.
    """

    def test_sales_agent_entry_point(self):
        assert callable(
            sales_agent.process_sales_request
        )

    def test_order_agent_entry_point(self):
        assert callable(
            order_agent.process_order
        )

    def test_support_agent_entry_point(self):
        assert callable(
            support_agent.answer_customer_question
        )

    def test_invoice_agent_entry_point(self):
        assert callable(
            invoice_agent.process_invoice_request
        )

    def test_payment_request_entry_point(self):
        assert callable(
            payment_agent.process_payment_request
        )

    def test_payment_completion_entry_point(self):
        assert callable(
            payment_agent.process_payment_completion
        )

    def test_payment_status_entry_point(self):
        assert callable(
            payment_agent.check_payment_status
        )