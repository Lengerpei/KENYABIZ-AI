import re

from src.graph import run_kenyabiz


# ============================================================
# KENYABIZ AI
# MAIN CLI APPLICATION
# ============================================================


class KenyaBizCLI:

    def __init__(self):

        # ----------------------------------------------------
        # Conversation state
        # ----------------------------------------------------
        self.conversation_history = []

        # ----------------------------------------------------
        # Active workflow
        # ----------------------------------------------------
        self.pending_request = None
        self.pending_action = None

        # ----------------------------------------------------
        # Customer details
        # ----------------------------------------------------
        self.customer_name = None
        self.customer_phone = None
        self.customer_email = None

        # ----------------------------------------------------
        # Order state
        # ----------------------------------------------------
        self.order_confirmed = False
        self.order_reference = None
        self.order_status = None

        # ----------------------------------------------------
        # Invoice state
        # ----------------------------------------------------
        self.invoice_path = None

        # ----------------------------------------------------
        # Payment state
        # ----------------------------------------------------
        self.payment_reference = None


    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.conversation_history = []

        self.pending_request = None
        self.pending_action = None

        self.customer_name = None
        self.customer_phone = None
        self.customer_email = None

        self.order_confirmed = False
        self.order_reference = None
        self.order_status = None

        self.invoice_path = None

        self.payment_reference = None


    # ========================================================
    # TEXT NORMALIZATION
    # ========================================================

    def normalize_text(self, text):

        if not text:
            return ""

        return " ".join(
            text.lower().strip().split()
        )


    # ========================================================
    # CONFIRMATION DETECTION
    # ========================================================

    def contains_confirmation(self, message):

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

        normalized = self.normalize_text(message)

        negatives = {
            "no",
            "no thanks",
            "no thank you",
            "cancel",
            "cancel it",
            "don't proceed",
            "do not proceed",
            "stop",
        }

        return normalized in negatives


    # ========================================================
    # ORDER REQUEST DETECTION
    # ========================================================

    def contains_order_request(self, message):

        normalized = self.normalize_text(message)

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

        return any(
            phrase in normalized
            for phrase in order_phrases
        )


    # ========================================================
    # INVOICE REQUEST DETECTION
    # ========================================================

    def contains_invoice_request(self, message):

        normalized = self.normalize_text(message)

        invoice_phrases = [
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
            phrase in normalized
            for phrase in invoice_phrases
        )


    # ========================================================
    # PAYMENT REQUEST
    # ========================================================

    def contains_payment_request(self, message):

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
        ]

        return any(
            phrase in normalized
            for phrase in payment_phrases
        )


    # ========================================================
    # PAYMENT COMPLETION
    # ========================================================

    def contains_payment_completion_request(self, message):

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

        if not message:
            return None

        text = message.strip()

        # ----------------------------------------------------
        # Explicit name formats
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Plain name
        # ----------------------------------------------------

        if self.looks_like_name(text):
            return text

        return None


    # ========================================================
    # NAME VALIDATION
    # ========================================================

    def looks_like_name(self, text):

        if not text:
            return False

        text = text.strip()

        if len(text) < 2:
            return False

        if len(text) > 100:
            return False

        # ----------------------------------------------------
        # Common non-name responses
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Names should not contain sentence punctuation
        # ----------------------------------------------------

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

        if not message:
            return None

        pattern = (
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}\b"
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

        if not result:
            return

        # ----------------------------------------------------
        # Order reference
        # ----------------------------------------------------

        order_reference = result.get(
            "order_reference"
        )

        if order_reference:
            self.order_reference = order_reference

        # ----------------------------------------------------
        # Order status
        # ----------------------------------------------------

        order_status = result.get(
            "order_status"
        )

        if order_status:
            self.order_status = order_status

        # ----------------------------------------------------
        # Payment reference
        # ----------------------------------------------------

        payment_reference = result.get(
            "payment_reference"
        )

        if payment_reference:
            self.payment_reference = (
                payment_reference
            )

        # ----------------------------------------------------
        # Invoice
        # ----------------------------------------------------

        invoice_path = result.get(
            "invoice_path"
        )

        if invoice_path:
            self.invoice_path = invoice_path

        # ----------------------------------------------------
        # Customer
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Nested payment result
        # ----------------------------------------------------

        payment = result.get("payment")

        if isinstance(payment, dict):

            nested_payment_reference = payment.get(
                "payment_reference"
            )

            if nested_payment_reference:
                self.payment_reference = (
                    nested_payment_reference
                )

            nested_order_reference = payment.get(
                "order_reference"
            )

            if nested_order_reference:
                self.order_reference = (
                    nested_order_reference
                )


    # ========================================================
    # UPDATE PENDING ACTION
    # ========================================================

    def update_pending_action(self, result):

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

        response = result.get(
            "response",
            ""
        )

        response_lower = response.lower()

        # ====================================================
        # ORDER WORKFLOW
        # ====================================================

        if destination == "order":

            # ------------------------------------------------
            # Waiting for confirmation
            # ------------------------------------------------

            if order_status == "AWAITING_CONFIRMATION":

                self.pending_action = (
                    "ORDER_CONFIRMATION"
                )

                self.pending_request = (
                    result.get(
                        "pending_request"
                    )
                    or self.pending_request
                )

                return

            # ------------------------------------------------
            # Waiting for customer name/details
            # ------------------------------------------------

            if order_status == "CUSTOMER_DETAILS_REQUIRED":

                self.pending_action = (
                    "CUSTOMER_NAME"
                )

                self.pending_request = (
                    result.get(
                        "pending_request"
                    )
                    or self.pending_request
                )

                return

            # ------------------------------------------------
            # Other order waiting states
            # ------------------------------------------------

            if order_status in {
                "AMBIGUOUS_PRODUCT",
                "PRODUCT_NOT_FOUND",
                "INSUFFICIENT_STOCK",
            }:

                self.pending_action = (
                    "ORDER_WORKFLOW"
                )

                self.pending_request = (
                    result.get(
                        "pending_request"
                    )
                    or self.pending_request
                )

                return

            # ------------------------------------------------
            # Order completed
            # ------------------------------------------------

            if status == "COMPLETED":

                if result.get(
                    "order_reference"
                ):

                    self.order_reference = (
                        result["order_reference"]
                    )

                self.pending_action = (
                    "ORDER_REFERENCE"
                )

                self.pending_request = None

                return

            # ------------------------------------------------
            # Response-based fallback
            # ------------------------------------------------

            if (
                "please confirm" in response_lower
                or "confirm that you would like" in response_lower
            ):

                self.pending_action = (
                    "ORDER_CONFIRMATION"
                )

                return

            if (
                "provide your name" in response_lower
                or "your name" in response_lower
            ):

                self.pending_action = (
                    "CUSTOMER_NAME"
                )

                return


        # ====================================================
        # INVOICE WORKFLOW
        # ====================================================

        if destination == "invoice":

            if result.get(
                "invoice_path"
            ):

                self.pending_action = (
                    "INVOICE_REFERENCE"
                )

                self.pending_request = None

                return

            if result.get(
                "order_reference"
            ):

                self.pending_action = (
                    "INVOICE_REFERENCE"
                )

                self.pending_request = None

                return


        # ====================================================
        # PAYMENT WORKFLOW
        # ====================================================

        if destination == "payment":

            payment_status = result.get(
                "payment_status"
            )

            payment = result.get(
                "payment"
            )

            if isinstance(payment, dict):

                payment_status = (
                    payment.get(
                        "payment_status"
                    )
                    or payment_status
                )

            if payment_status:

                payment_status = str(
                    payment_status
                ).upper()

            if payment_status in {
                "PENDING",
                "PAID",
                "COMPLETED",
                "SUCCESS",
            }:

                self.pending_action = (
                    "PAYMENT_REFERENCE"
                )

                self.pending_request = None

                return

            if self.payment_reference:

                self.pending_action = (
                    "PAYMENT_REFERENCE"
                )

                self.pending_request = None

                return


        # ====================================================
        # GENERAL COMPLETION
        # ====================================================

        if status == "COMPLETED":

            if destination not in {
                "order",
                "invoice",
                "payment",
            }:

                self.pending_action = None
                self.pending_request = None


    # ========================================================
    # RUN AGENT
    # ========================================================

    def _run_agent(
        self,
        message,
        forced_destination=None,
    ):

        result = run_kenyabiz(
            customer_message=message,
            forced_destination=forced_destination,
            pending_request=self.pending_request,
            order_confirmed=self.order_confirmed,
        )

        if not result:

            response = (
                "I was unable to process your request."
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

        # ----------------------------------------------------
        # Confirmation state
        # ----------------------------------------------------

        if result.get(
            "order_confirmed"
        ) is not None:

            self.order_confirmed = (
                result.get(
                    "order_confirmed"
                )
            )

        # ----------------------------------------------------
        # Pending request
        # ----------------------------------------------------

        if result.get(
            "pending_request"
        ):

            self.pending_request = (
                result.get(
                    "pending_request"
                )
            )

        # ----------------------------------------------------
        # Pending action
        # ----------------------------------------------------

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
                "I was unable to generate a response."
            )

        self.save_assistant_message(
            response
        )

        return response


    # ========================================================
    # HANDLE MESSAGE
    # ========================================================

    def handle_message(self, message):

        if not message:
            return "Please enter a message."

        message = message.strip()

        if not message:
            return "Please enter a message."

        # ----------------------------------------------------
        # Save user message
        # ----------------------------------------------------

        self.save_customer_message(
            message
        )


        # ====================================================
        # 1. ACTIVE ORDER CONFIRMATION
        # ====================================================

        if (
            self.pending_action
            == "ORDER_CONFIRMATION"
        ):

            # ------------------------------------------------
            # Customer confirmed
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Customer cancelled
            # ------------------------------------------------

            if self.contains_negative_confirmation(
                message
            ):

                self.pending_action = None
                self.pending_request = None
                self.order_confirmed = False

                response = (
                    "No problem. The order has not "
                    "been created."
                )

                self.save_assistant_message(
                    response
                )

                return response


        # ====================================================
        # 2. CUSTOMER NAME
        # ====================================================

        if (
            self.pending_action
            == "CUSTOMER_NAME"
        ):

            name = self.extract_name(
                message
            )

            if name:

                self.customer_name = name

                # --------------------------------------------
                # Preserve original order request
                # --------------------------------------------

                order_request = (
                    self.pending_request
                    or "Create the customer's order."
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
        # 3. OTHER ACTIVE ORDER WORKFLOW
        # ====================================================

        if (
            self.pending_action
            == "ORDER_WORKFLOW"
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

            # -----------------------------------------------
            # Capture customer information
            # -----------------------------------------------

            self.update_customer_details(
                message
            )

            if self.customer_name:

                order_message = (
                    self.pending_request
                    or message
                )

                order_message += (
                    "\n\nCustomer name: "
                    + self.customer_name
                )

                return self._run_agent(
                    message=order_message,
                    forced_destination="order",
                )


        # ====================================================
        # 4. ACTIVE INVOICE WORKFLOW
        # ====================================================

        if (
            self.pending_action
            == "INVOICE_REFERENCE"
        ):

            # ------------------------------------------------
            # PAYMENT HAS PRIORITY
            # ------------------------------------------------

            if self.contains_payment_completion_request(
                message
            ):

                if self.payment_reference:

                    payment_message = (
                        f"Complete payment "
                        f"{self.payment_reference}"
                    )

                    return self._run_agent(
                        message=payment_message,
                        forced_destination="payment",
                    )

                return self._run_agent(
                    message=message,
                    forced_destination="payment",
                )

            # ------------------------------------------------
            # Payment status
            # ------------------------------------------------

            if self.contains_payment_status_request(
                message
            ):

                if self.payment_reference:

                    payment_message = (
                        f"Check payment status for "
                        f"{self.payment_reference}"
                    )

                    return self._run_agent(
                        message=payment_message,
                        forced_destination="payment",
                    )

                return self._run_agent(
                    message=message,
                    forced_destination="payment",
                )

            # ------------------------------------------------
            # New payment request
            # ------------------------------------------------

            if self.contains_payment_request(
                message
            ):

                if self.order_reference:

                    payment_message = (
                        f"Create payment request "
                        f"for order "
                        f"{self.order_reference}"
                    )

                    return self._run_agent(
                        message=payment_message,
                        forced_destination="payment",
                    )

                return self._run_agent(
                    message=message,
                    forced_destination="payment",
                )

            # ------------------------------------------------
            # Continue invoice workflow
            # ------------------------------------------------

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

                invoice_message = (
                    f"Generate invoice for order "
                    f"{self.order_reference}"
                )

                return self._run_agent(
                    message=invoice_message,
                    forced_destination="invoice",
                )


        # ====================================================
        # 5. PAYMENT COMPLETION
        # ====================================================

        if self.contains_payment_completion_request(
            message
        ):

            if self.payment_reference:

                payment_message = (
                    f"Complete payment "
                    f"{self.payment_reference}"
                )

                return self._run_agent(
                    message=payment_message,
                    forced_destination="payment",
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

            if self.payment_reference:

                payment_message = (
                    f"Check payment status for "
                    f"{self.payment_reference}"
                )

                return self._run_agent(
                    message=payment_message,
                    forced_destination="payment",
                )

            return self._run_agent(
                message=message,
                forced_destination="payment",
            )


        # ====================================================
        # 7. NEW PAYMENT REQUEST
        # ====================================================

        if self.contains_payment_request(
            message
        ):

            if self.order_reference:

                payment_message = (
                    f"Create payment request "
                    f"for order "
                    f"{self.order_reference}"
                )

                return self._run_agent(
                    message=payment_message,
                    forced_destination="payment",
                )

            return self._run_agent(
                message=message,
                forced_destination="payment",
            )


        # ====================================================
        # 8. ACTIVE PAYMENT REFERENCE
        # ====================================================
        #
        # IMPORTANT:
        # Having a payment reference does NOT mean that
        # every future message belongs to the Payment Agent.
        #
        # We only continue the payment workflow if:
        #
        #   1. The customer provides a payment reference, OR
        #   2. The customer explicitly asks for payment status.
        #
        # Otherwise, execution falls through to the normal
        # Supervisor routing.
        #
        # This allows questions such as:
        #
        #   "What products do you have?"
        #   "How long does delivery take?"
        #   "Do you provide invoices?"
        #
        # to reach the correct specialist agent.
        # ====================================================

        if self.pending_action == "PAYMENT_REFERENCE":

            # ------------------------------------------------
            # Customer provides a payment reference
            # ------------------------------------------------

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
                    f"Check payment status for "
                    f"{self.payment_reference}"
                )

                return self._run_agent(
                    message=payment_message,
                    forced_destination="payment",
                )

            # ------------------------------------------------
            # Customer explicitly asks for payment status
            # ------------------------------------------------

            if self.contains_payment_status_request(
                message
            ):

                if self.payment_reference:

                    payment_message = (
                        f"Check payment status for "
                        f"{self.payment_reference}"
                    )

                    return self._run_agent(
                        message=payment_message,
                        forced_destination="payment",
                    )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # Do NOT return here.
            #
            # If the message is unrelated to payment,
            # execution falls through to the normal
            # Supervisor routing below.
            # ------------------------------------------------


        # ====================================================
        # 9. EXPLICIT INVOICE REQUEST
        # ====================================================

        if self.contains_invoice_request(
            message
        ):

            if self.order_reference:

                invoice_message = (
                    f"Generate invoice for order "
                    f"{self.order_reference}"
                )

                return self._run_agent(
                    message=invoice_message,
                    forced_destination="invoice",
                )

            return self._run_agent(
                message=message,
                forced_destination="invoice",
            )


        # ====================================================
        # 10. NEW ORDER REQUEST
        # ====================================================

        if self.contains_order_request(
            message
        ):

            self.order_confirmed = False

            # -----------------------------------------------
            # Preserve original order request
            # -----------------------------------------------

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
        # 11. PAYMENT REFERENCE IN MESSAGE
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
                f"Check payment status for "
                f"{payment_reference}"
            )

            return self._run_agent(
                message=payment_message,
                forced_destination="payment",
            )


        # ====================================================
        # 12. ORDER REFERENCE IN MESSAGE
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
        # 13. NORMAL REQUEST
        # ====================================================

        return self._run_agent(
            message=message,
            forced_destination=None,
        )


    # ========================================================
    # MAIN CLI
    # ========================================================

    def main(self):

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

            normalized = (
                self.normalize_text(
                    message
                )
            )

            # ------------------------------------------------
            # Exit
            # ------------------------------------------------

            if normalized in {
                "exit",
                "quit",
                "bye",
                "goodbye",
            }:

                print()

                print(
                    "KenyaBiz AI: Goodbye!"
                )

                break


            # ------------------------------------------------
            # Reset
            # ------------------------------------------------

            if normalized in {
                "reset",
                "start over",
                "new conversation",
            }:

                self.reset()

                print()

                print(
                    "KenyaBiz AI: "
                    "The conversation has been reset."
                )

                print()

                continue


            # ------------------------------------------------
            # Process
            # ------------------------------------------------

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

            print()

            print(
                "KenyaBiz AI:"
            )

            print(
                response
            )

            print()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================


def main():

    app = KenyaBizCLI()

    app.main()


if __name__ == "__main__":

    main()