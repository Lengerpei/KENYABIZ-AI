import re

from src.graph import run_kenyabiz


# ============================================================
# KENYABIZ AI
# MAIN CONVERSATION / CLI APPLICATION
# ============================================================


class KenyaBizConversation:
    """
    Conversation and session manager for KenyaBiz AI.

    This class maintains customer conversation state between
    calls to the LangGraph workflow.

    The business logic and specialist routing remain in the
    graph and agent layers.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self):
        self.reset()

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):
        """Reset the current conversation and workflow state."""

        # Conversation memory
        self.conversation_history = []

        # Pending workflow
        self.pending_request = None
        self.pending_action = None

        # Customer details
        self.customer_name = None
        self.customer_phone = None
        self.customer_email = None

        # Order state
        self.order_confirmed = False
        self.order_reference = None
        self.order_status = None

        # Invoice state
        self.invoice_path = None

        # Payment state
        self.payment_reference = None
        self.payment_status = None

    # ========================================================
    # TEXT NORMALIZATION
    # ========================================================

    @staticmethod
    def normalize_text(text):
        """Normalize text for simple intent checks."""

        if not text:
            return ""

        return " ".join(
            str(text).lower().strip().split()
        )

    # ========================================================
    # CONFIRMATION DETECTION
    # ========================================================

    def contains_confirmation(self, message):
        """Return True when the message clearly confirms an action."""

        normalized = self.normalize_text(message)

        confirmations = {
            "yes",
            "yes please",
            "sure",
            "sure please",
            "okay",
            "ok",
            "okay please",
            "proceed",
            "please proceed",
            "go ahead",
            "go ahead please",
            "confirm",
            "confirmed",
            "i confirm",
            "confirm order",
            "confirm the order",
            "place the order",
            "place order",
            "i want to proceed",
            "that's correct",
            "that is correct",
            "correct",
        }

        return normalized in confirmations

    # ========================================================
    # NEGATIVE CONFIRMATION
    # ========================================================

    def contains_negative_confirmation(self, message):
        """Return True when the message clearly declines an action."""

        normalized = self.normalize_text(message)

        negatives = {
            "no",
            "no thanks",
            "no thank you",
            "cancel",
            "cancel it",
            "cancel the order",
            "don't proceed",
            "do not proceed",
            "stop",
        }

        return normalized in negatives

    # ========================================================
    # ORDER REQUEST DETECTION
    # ========================================================

    def contains_order_request(self, message):
        """
        Detect an explicit request to purchase/order a product.

        Product recognition is deliberately broader than the old
        chair/desk-only implementation because the KenyaBiz
        catalogue contains multiple product categories.
        """

        normalized = self.normalize_text(message)

        if not normalized:
            return False

        order_phrases = [
            "i want to order",
            "i would like to order",
            "i'd like to order",
            "i need to order",
            "place an order",
            "place order",
            "make an order",
            "buy",
            "purchase",
            "i want to buy",
            "i would like to buy",
            "i'd like to buy",
        ]

        product_terms = [
            # Furniture
            "chair",
            "chairs",
            "office chair",
            "office chairs",
            "visitor chair",
            "visitor chairs",
            "desk",
            "desks",
            "office desk",
            "office desks",
            "executive desk",
            "executive desks",
            "cabinet",
            "cabinets",
            "office cabinet",
            "office cabinets",
            "meeting table",
            "meeting tables",
            "table",
            "tables",

            # Accessories
            "laptop stand",
            "laptop stands",
            "monitor stand",
            "monitor stands",
            "keyboard",
            "keyboards",
            "mouse",
            "mice",
            "wireless mouse",
            "wireless mice",

            # Other possible catalogue terms
            "laptop",
            "laptops",
            "phone",
            "phones",
            "printer",
            "printers",
            "monitor",
            "monitors",
        ]

        has_order_phrase = any(
            phrase in normalized
            for phrase in order_phrases
        )

        has_product = any(
            product in normalized
            for product in product_terms
        )

        return has_order_phrase and has_product

    # ========================================================
    # INVOICE REQUEST DETECTION
    # ========================================================

    def contains_invoice_request(self, message):
        """Detect invoice, billing, or receipt requests."""

        normalized = self.normalize_text(message)

        invoice_terms = [
            "invoice",
            "invoicing",
            "bill",
            "billing",
            "receipt",
            "my invoice",
            "the invoice",
            "i want my invoice",
            "i need my invoice",
            "get my invoice",
            "send my invoice",
            "generate an invoice",
            "generate invoice",
            "create an invoice",
            "create invoice",
            "make an invoice",
            "make invoice",
            "get an invoice",
            "get invoice",
            "invoice for my order",
            "send me an invoice",
            "i need an invoice",
            "i want an invoice",
        ]

        return any(
            term in normalized
            for term in invoice_terms
        )

    # ========================================================
    # PAYMENT REQUEST
    # ========================================================

    def contains_payment_request(self, message):
        """Detect a request to initiate a payment."""

        normalized = self.normalize_text(message)

        payment_phrases = [
            "make payment",
            "make a payment",
            "make the payment",
            "i want to make payment",
            "i want to make a payment",
            "i would like to make payment",
            "i would like to make a payment",
            "i'd like to make payment",
            "i'd like to make a payment",
            "i want to pay",
            "i would like to pay",
            "i'd like to pay",
            "i want to pay for",
            "i would like to pay for",
            "i'd like to pay for",
            "pay for my order",
            "pay my order",
            "payment for my order",
            "make payment for my order",
            "make a payment for my order",
            "payment for",
            "pay for",
            "start payment",
            "start a payment",
            "initiate payment",
            "initiate a payment",
            "create a payment",
            "create payment",
            "create a payment request",
            "create payment request",
            "payment request for",
            "send me the payment request",
            "send payment request",
            "pay now",
            "mpesa",
            "m-pesa",
            "m pesa",
        ]

        return any(
            phrase in normalized
            for phrase in payment_phrases
        )

    # ========================================================
    # PAYMENT COMPLETION
    # ========================================================

    def contains_payment_completion_request(self, message):
        """Detect a request to mark/complete an existing payment."""

        normalized = self.normalize_text(message)

        completion_phrases = [
            "i have paid",
            "i paid",
            "i have made the payment",
            "i made the payment",
            "i have completed the payment",
            "i've completed the payment",
            "i have completed payment",
            "i've completed payment",
            "payment made",
            "payment is complete",
            "the payment is complete",
            "payment completed",
            "payment has been completed",
            "the payment has been completed",
            "complete payment",
            "complete the payment",
            "confirm payment",
            "confirm the payment",
            "mark as paid",
            "mark payment as paid",
            "paid already",
        ]

        return any(
            phrase in normalized
            for phrase in completion_phrases
        )

    # ========================================================
    # PAYMENT STATUS
    # ========================================================

    def contains_payment_status_request(self, message):
        """Detect a request to check payment status."""

        normalized = self.normalize_text(message)

        status_phrases = [
            "payment status",
            "what is my payment status",
            "what's my payment status",
            "what is the payment status",
            "what's the payment status",
            "check payment status",
            "check my payment status",
            "check the payment status",
            "payment status check",
            "has my payment gone through",
            "is my payment complete",
            "is my payment completed",
            "is the payment complete",
            "is the payment completed",
            "did my payment go through",
            "did the payment go through",
            "was my payment successful",
            "was the payment successful",
        ]

        return any(
            phrase in normalized
            for phrase in status_phrases
        )

    # ========================================================
    # NAME EXTRACTION
    # ========================================================

    def extract_name(self, message):
        """Extract a customer name from common natural-language forms."""

        if not message:
            return None

        text = message.strip()

        patterns = [
            r"^(?:my name is|i am|i'm|name is)\s+(.+)$",
            r"^(?:this is)\s+(.+)$",
        ]

        for pattern in patterns:
            match = re.match(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                name = match.group(1).strip()

                if self.looks_like_name(name):
                    return name

        # Plain name, for example:
        #
        # Ambrose Lengerpei
        if self.looks_like_name(text):
            return text

        return None

    # ========================================================
    # NAME VALIDATION
    # ========================================================

    def looks_like_name(self, text):
        """Basic validation to distinguish names from normal messages."""

        if not text:
            return False

        text = text.strip()

        if len(text) < 2:
            return False

        if len(text) > 100:
            return False

        forbidden = {
            "yes",
            "no",
            "okay",
            "ok",
            "sure",
            "proceed",
            "confirm",
            "confirmed",
            "please",
            "thanks",
            "thank you",
        }

        normalized = self.normalize_text(text)

        if normalized in forbidden:
            return False

        if any(
            character in text
            for character in [
                "?",
                "!",
                ".",
                ",",
                ":",
                ";",
            ]
        ):
            return False

        words = text.split()

        if len(words) > 5:
            return False

        for word in words:
            cleaned = (
                word
                .replace("-", "")
                .replace("'", "")
            )

            if not cleaned.isalpha():
                return False

        return True

    # ========================================================
    # PHONE EXTRACTION
    # ========================================================

    def extract_phone(self, message):
        """Extract a Kenyan mobile phone number."""

        if not message:
            return None

        pattern = (
            r"(?:\+254|254|0)"
            r"(?:7|1)\d{8}\b"
        )

        cleaned_message = message.replace(
            " ",
            "",
        )

        match = re.search(
            pattern,
            cleaned_message,
        )

        if not match:
            return None

        return match.group(0)

    # ========================================================
    # EMAIL EXTRACTION
    # ========================================================

    def extract_email(self, message):
        """Extract an email address."""

        if not message:
            return None

        pattern = (
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+"
            r"\.[A-Za-z]{2,}\b"
        )

        match = re.search(
            pattern,
            message,
        )

        if not match:
            return None

        return match.group(0)

    # ========================================================
    # ORDER REFERENCE
    # ========================================================

    def extract_order_reference(self, message):
        """Extract a KenyaBiz order reference."""

        if not message:
            return None

        pattern = r"\bKBA-\d{8}-[A-Z0-9]+\b"

        match = re.search(
            pattern,
            message.upper(),
        )

        if not match:
            return None

        return match.group(0)

    # ========================================================
    # PAYMENT REFERENCE
    # ========================================================

    def extract_payment_reference(self, message):
        """Extract a simulated M-PESA payment reference."""

        if not message:
            return None

        pattern = r"\bMPS[A-Z0-9]+\b"

        match = re.search(
            pattern,
            message.upper(),
        )

        if not match:
            return None

        return match.group(0)

    # ========================================================
    # UPDATE CUSTOMER DETAILS
    # ========================================================

    def update_customer_details(self, message):
        """Update stored customer information when supplied."""

        changed = False

        name = self.extract_name(message)

        if name:
            self.customer_name = name
            changed = True

        phone = self.extract_phone(message)

        if phone:
            self.customer_phone = phone
            changed = True

        email = self.extract_email(message)

        if email:
            self.customer_email = email
            changed = True

        return changed

    # ========================================================
    # BUILD ORDER MESSAGE
    # ========================================================

    def build_order_message(self, message):
        """
        Add known customer information to an order message
        before sending it to the Order Agent.
        """

        parts = [message]

        if self.customer_name:
            parts.append(
                f"Customer name: {self.customer_name}"
            )

        if self.customer_phone:
            parts.append(
                f"Customer phone: {self.customer_phone}"
            )

        if self.customer_email:
            parts.append(
                f"Customer email: {self.customer_email}"
            )

        return "\n".join(parts)

    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    def save_customer_message(self, message):
        """Add a customer message to conversation history."""

        self.conversation_history.append(
            {
                "role": "user",
                "content": message,
            }
        )

    # ========================================================
    # SAVE ASSISTANT MESSAGE
    # ========================================================

    def save_assistant_message(self, message):
        """Add an assistant response to conversation history."""

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": message,
            }
        )

    # ========================================================
    # UPDATE STATE FROM GRAPH RESULT
    # ========================================================

    def _update_from_result(self, result):
        """Persist relevant fields returned by LangGraph."""

        if not result:
            return

        order_reference = result.get(
            "order_reference"
        )

        if order_reference:
            self.order_reference = order_reference

        order_status = result.get(
            "order_status"
        )

        if order_status:
            self.order_status = order_status

        payment_reference = result.get(
            "payment_reference"
        )

        if payment_reference:
            self.payment_reference = payment_reference

        payment_status = result.get(
            "payment_status"
        )

        if payment_status:
            self.payment_status = payment_status

        invoice_path = result.get(
            "invoice_path"
        )

        if invoice_path:
            self.invoice_path = invoice_path

        customer_name = result.get(
            "customer_name"
        )

        if customer_name:
            self.customer_name = customer_name

        customer_phone = result.get(
            "customer_phone"
        )

        if customer_phone:
            self.customer_phone = customer_phone

        customer_email = result.get(
            "customer_email"
        )

        if customer_email:
            self.customer_email = customer_email

    # ========================================================
    # UPDATE PENDING ACTION
    # ========================================================

    def update_pending_action(self, result):
        """Synchronize local workflow state with graph output."""

        if not result:
            return

        destination = result.get(
            "destination"
        )

        status = result.get(
            "status"
        )

        order_status = result.get(
            "order_status"
        )

        pending_action = result.get(
            "pending_action"
        )

        pending_request = result.get(
            "pending_request"
        )

        # ----------------------------------------------------
        # Preserve explicit graph state
        # ----------------------------------------------------

        if pending_action is not None:
            self.pending_action = pending_action

        if pending_request is not None:
            self.pending_request = pending_request

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        if destination == "order":

            if order_status == "AWAITING_CONFIRMATION":
                self.pending_action = (
                    "ORDER_CONFIRMATION"
                )
                return

            if order_status == "CUSTOMER_DETAILS_REQUIRED":
                self.pending_action = (
                    "ORDER_CUSTOMER_NAME"
                )
                return

            if status == "COMPLETED":
                self.pending_action = None
                self.pending_request = None
                return

            response = result.get(
                "response",
                "",
            )

            response_lower = response.lower()

            if (
                "please confirm" in response_lower
                or
                "confirm that you would like"
                in response_lower
            ):
                self.pending_action = (
                    "ORDER_CONFIRMATION"
                )
                return

            if (
                "provide your name" in response_lower
                or
                "your name" in response_lower
            ):
                self.pending_action = (
                    "ORDER_CUSTOMER_NAME"
                )
                return

        # ----------------------------------------------------
        # INVOICE
        # ----------------------------------------------------

        if destination == "invoice":

            if pending_action == (
                "INVOICE_ORDER_REFERENCE"
            ):
                self.pending_action = (
                    "INVOICE_ORDER_REFERENCE"
                )
                return

            if status == "COMPLETED":
                self.pending_action = None
                self.pending_request = None
                return

            if self.invoice_path:
                self.pending_action = None
                self.pending_request = None
                return

        # ----------------------------------------------------
        # PAYMENT
        # ----------------------------------------------------

        if destination == "payment":

            if pending_action == (
                "PAYMENT_ORDER_REFERENCE"
            ):
                self.pending_action = (
                    "PAYMENT_ORDER_REFERENCE"
                )
                return

            if status == "COMPLETED":
                self.pending_action = None
                self.pending_request = None
                return

    # ========================================================
    # RUN LANGGRAPH
    # ========================================================

    def _run_agent(
        self,
        message,
        forced_destination=None,
    ):
        """
        Send the current message and conversation state
        to the LangGraph workflow.
        """

        result = run_kenyabiz(
            customer_message=message,

            forced_destination=forced_destination,

            conversation_history=(
                self.conversation_history
            ),

            pending_request=(
                self.pending_request
            ),

            order_confirmed=(
                self.order_confirmed
            ),

            pending_action=(
                self.pending_action
            ),

            order_reference=(
                self.order_reference
            ),

            order_status=(
                self.order_status
            ),

            invoice_path=(
                self.invoice_path
            ),

            payment_reference=(
                self.payment_reference
            ),

            payment_status=(
                self.payment_status
            ),
        )

        if not result:
            response = (
                "I was unable to process "
                "your request."
            )

            self.save_assistant_message(
                response
            )

            return response

        # ----------------------------------------------------
        # Update state
        # ----------------------------------------------------

        self._update_from_result(
            result
        )

        if result.get(
            "order_confirmed"
        ) is not None:
            self.order_confirmed = (
                result.get(
                    "order_confirmed"
                )
            )

        if "pending_request" in result:
            self.pending_request = (
                result.get(
                    "pending_request"
                )
            )

        self.update_pending_action(
            result
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        response = result.get(
            "response"
        )

        if not response:
            response = result.get(
                "message"
            )

        if not response:
            response = (
                "I was unable to generate "
                "a response."
            )

        self.save_assistant_message(
            response
        )

        return response

    # ========================================================
    # HANDLE MESSAGE
    # ========================================================

    def handle_message(self, message):
        """
        Process one customer message.

        This method manages conversation/session state while
        LangGraph remains responsible for specialist routing
        and business processing.
        """

        if not message:
            return "Please enter a message."

        message = message.strip()

        if not message:
            return "Please enter a message."

        normalized = self.normalize_text(
            message
        )

        # ====================================================
        # EXIT
        # ====================================================

        if normalized in {
            "exit",
            "quit",
            "bye",
            "goodbye",
        }:
            return "Goodbye!"

        # ====================================================
        # RESET
        # ====================================================

        if normalized in {
            "reset",
            "start over",
            "new conversation",
        }:
            self.reset()

            return (
                "The conversation has been reset."
            )

        # ====================================================
        # SAVE CUSTOMER MESSAGE
        # ====================================================

        self.save_customer_message(
            message
        )

        # ====================================================
        # UPDATE CUSTOMER DETAILS
        # ====================================================

        self.update_customer_details(
            message
        )

        # ====================================================
        # 1. ACTIVE ORDER CONFIRMATION
        # ====================================================

        if (
            self.pending_action
            == "ORDER_CONFIRMATION"
        ):

            if self.contains_confirmation(
                message
            ):

                self.order_confirmed = True

                confirmation_message = (
                    "Customer confirmed the order."
                )

                if self.pending_request:
                    confirmation_message += (
                        "\n\n"
                        + self.pending_request
                    )

                return self._run_agent(
                    message=confirmation_message,
                    forced_destination="order",
                )

            if self.contains_negative_confirmation(
                message
            ):

                # Let the graph/order workflow handle
                # the cancellation consistently.
                cancellation_message = (
                    "Customer declined the order."
                )

                return self._run_agent(
                    message=cancellation_message,
                    forced_destination="order",
                )

        # ====================================================
        # 2. CUSTOMER NAME FOR ORDER
        # ====================================================

        if self.pending_action in {
            "ORDER_CUSTOMER_NAME",
            "CUSTOMER_NAME",
        }:

            # ------------------------------------------------
            # Allow invoice request to interrupt order flow
            # ------------------------------------------------

            if self.contains_invoice_request(
                message
            ):

                order_reference = (
                    self.extract_order_reference(
                        message
                    )
                )

                if order_reference:

                    self.order_reference = (
                        order_reference
                    )

                    self.pending_request = None
                    self.pending_action = None
                    self.order_confirmed = False

                    invoice_message = (
                        "Generate invoice for order "
                        f"{order_reference}"
                    )

                    return self._run_agent(
                        message=invoice_message,
                        forced_destination="invoice",
                    )

            # ------------------------------------------------
            # Customer name
            # ------------------------------------------------

            name = self.extract_name(
                message
            )

            if name:

                self.customer_name = name

                order_request = (
                    self.pending_request
                    or
                    "Create the customer's order."
                )

                order_message = (
                    f"{order_request}\n\n"
                    f"Customer name: "
                    f"{self.customer_name}"
                )

                if self.customer_phone:
                    order_message += (
                        "\nCustomer phone: "
                        + self.customer_phone
                    )

                if self.customer_email:
                    order_message += (
                        "\nCustomer email: "
                        + self.customer_email
                    )

                return self._run_agent(
                    message=order_message,
                    forced_destination="order",
                )

            response = (
                "Please provide your name, "
                "for example: Ambrose Lengerpei."
            )

            self.save_assistant_message(
                response
            )

            return response

        # ====================================================
        # 3. ACTIVE INVOICE WORKFLOW
        # ====================================================

        if (
            self.pending_action
            == "INVOICE_ORDER_REFERENCE"
        ):

            order_reference = (
                self.extract_order_reference(
                    message
                )
            )

            if order_reference:

                self.order_reference = (
                    order_reference
                )

                self.pending_action = None
                self.pending_request = None

                invoice_message = (
                    "Generate invoice for order "
                    f"{order_reference}"
                )

                return self._run_agent(
                    message=invoice_message,
                    forced_destination="invoice",
                )

            response = (
                "Please provide a valid KenyaBiz "
                "order reference, for example "
                "KBA-20260930-B49N."
            )

            self.save_assistant_message(
                response
            )

            return response

        # ====================================================
        # 4. EXPLICIT INVOICE REQUEST
        # ====================================================

        if self.contains_invoice_request(
            message
        ):

            order_reference = (
                self.extract_order_reference(
                    message
                )
            )

            if order_reference:
                self.order_reference = (
                    order_reference
                )

            if self.order_reference:

                self.pending_request = None
                self.pending_action = None
                self.order_confirmed = False

                invoice_message = (
                    "Generate invoice for order "
                    f"{self.order_reference}"
                )

                return self._run_agent(
                    message=invoice_message,
                    forced_destination="invoice",
                )

            self.pending_request = None

            self.pending_action = (
                "INVOICE_ORDER_REFERENCE"
            )

            return self._run_agent(
                message=message,
                forced_destination="invoice",
            )

        # ====================================================
        # 5. PAYMENT COMPLETION
        # ====================================================

        if self.contains_payment_completion_request(
            message
        ):

            payment_reference = (
                self.extract_payment_reference(
                    message
                )
            )

            if payment_reference:
                self.payment_reference = (
                    payment_reference
                )

            order_reference = (
                self.extract_order_reference(
                    message
                )
            )

            if order_reference:
                self.order_reference = (
                    order_reference
                )

            return self._run_agent(
                message=message,
                forced_destination="payment",
            )

        # ====================================================
        # 6. PAYMENT STATUS
        # ====================================================

        if self.contains_payment_status_request(
            message
        ):

            payment_reference = (
                self.extract_payment_reference(
                    message
                )
            )

            if payment_reference:
                self.payment_reference = (
                    payment_reference
                )

            return self._run_agent(
                message=message,
                forced_destination="payment",
            )

        # ====================================================
        # 7. PAYMENT REQUEST
        # ====================================================

        if self.contains_payment_request(
            message
        ):

            order_reference = (
                self.extract_order_reference(
                    message
                )
            )

            if order_reference:
                self.order_reference = (
                    order_reference
                )

            self.pending_request = None
            self.pending_action = None
            self.order_confirmed = False

            return self._run_agent(
                message=message,
                forced_destination="payment",
            )

        # ====================================================
        # 8. PAYMENT REFERENCE
        # ====================================================

        payment_reference = (
            self.extract_payment_reference(
                message
            )
        )

        if payment_reference:

            self.payment_reference = (
                payment_reference
            )

            payment_message = (
                "Check payment status for "
                f"{payment_reference}"
            )

            return self._run_agent(
                message=payment_message,
                forced_destination="payment",
            )

        # ====================================================
        # 9. NEW ORDER REQUEST
        # ====================================================

        if self.contains_order_request(
            message
        ):

            self.order_confirmed = False
            self.pending_request = message

            order_message = (
                self.build_order_message(
                    message
                )
            )

            return self._run_agent(
                message=order_message,
                forced_destination="order",
            )

        # ====================================================
        # 10. ORDER REFERENCE
        # ====================================================

        order_reference = (
            self.extract_order_reference(
                message
            )
        )

        if order_reference:
            self.order_reference = (
                order_reference
            )

        # ====================================================
        # 11. NORMAL REQUEST
        # ====================================================

        return self._run_agent(
            message=message,
            forced_destination=None,
        )

    # ========================================================
    # MAIN CLI
    # ========================================================

    def main(self):
        """Run the interactive command-line application."""

        print("=" * 70)
        print("KENYABIZ AI")
        print("MULTI-AGENT BUSINESS ASSISTANT")
        print("=" * 70)
        print()

        print(
            "Welcome to KenyaBiz AI."
        )

        print(
            "I can help with products, quotations, "
            "orders, invoices, payments, and support."
        )

        print()

        print(
            "Type 'exit' or 'quit' to end the conversation."
        )

        print(
            "Type 'reset' to start a new conversation."
        )

        print()

        while True:

            try:
                message = input(
                    "You: "
                ).strip()

            except (
                KeyboardInterrupt,
                EOFError,
            ):

                print()
                print(
                    "KenyaBiz AI: Goodbye!"
                )

                break

            if not message:
                continue

            try:

                response = self.handle_message(
                    message
                )

            except Exception as error:

                response = (
                    "I encountered an error while "
                    "processing your request: "
                    f"{error}"
                )

            # ------------------------------------------------
            # Handle exit after processing
            # ------------------------------------------------

            if self.normalize_text(
                message
            ) in {
                "exit",
                "quit",
                "bye",
                "goodbye",
            }:

                print()
                print(
                    "KenyaBiz AI:"
                )
                print(
                    response
                )
                print()

                break

            # ------------------------------------------------
            # Display response
            # ------------------------------------------------

            print()
            print(
                "KenyaBiz AI:"
            )
            print(
                response
            )
            print()


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

# Streamlit and any existing code that uses KenyaBizCLI
# can continue working.

KenyaBizCLI = KenyaBizConversation


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():
    app = KenyaBizConversation()
    app.main()


if __name__ == "__main__":
    main()