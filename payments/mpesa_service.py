"""
M-Pesa Daraja API Integration Service
Handles STK push, authentication, and transaction queries
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def create_session_with_retries(max_retries=3, backoff_factor=0.5):
    """
    Create a requests session with automatic retry logic
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class MpesaClient:
    """
    M-Pesa Daraja API client for STK push and payment verification
    Handles OAuth tokens, STK initiation, and transaction status queries
    """

    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.passkey = settings.MPESA_PASSKEY
        self.short_code = settings.MPESA_SHORT_CODE
        self.till_number = settings.MPESA_TILL_NUMBER
        self.environment = settings.MPESA_ENVIRONMENT  # 'sandbox' or 'production'
        
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'

        self.auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        self.stk_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        self.query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        self.transaction_type = getattr(settings, 'MPESA_TRANSACTION_TYPE', 'CustomerBuyGoodsOnline')

    def authenticate(self):
        """
        Get OAuth token from M-Pesa
        Tokens valid for 1 hour, cached to reduce API calls
        Includes automatic retry logic for transient failures
        Returns: access_token string or None if failed
        """
        # Check cache first
        cached_token = cache.get('mpesa_access_token')
        if cached_token:
            logger.info("Using cached M-Pesa token")
            return cached_token

        try:
            session = create_session_with_retries(max_retries=3, backoff_factor=0.5)
            response = session.get(
                self.auth_url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=10
            )
            response.raise_for_status()
            
            token = response.json().get('access_token')
            if token:
                # Cache for 55 minutes (token valid for 1 hour)
                cache.set('mpesa_access_token', token, 55 * 60)
                logger.info("M-Pesa authentication successful")
                return token
            else:
                logger.error(f"No token in M-Pesa response: {response.json()}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"M-Pesa authentication failed after retries: {str(e)}", exc_info=True)
            return None

    def initiate_stk_push(self, phone_number, amount, reference_id, description=""):
        """
        Trigger STK push to user's phone for M-Pesa payment
        
        Args:
            phone_number: Valid Safaricom number (254XXXXXXXXX format)
            amount: Amount in KES (as integer)
            reference_id: Unique reference for this transaction (Payment ID)
            description: Transaction description
            
        Returns:
            {
                'success': bool,
                'checkout_request_id': str or None,
                'response_code': str,
                'message': str
            }
        """
        token = self.authenticate()
        if not token:
            return {
                'success': False,
                'checkout_request_id': None,
                'response_code': 'AUTH_FAILED',
                'message': 'Failed to authenticate with M-Pesa'
            }

        # Normalize phone number
        if not phone_number.startswith('254'):
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            else:
                phone_number = '254' + phone_number

        # Generate timestamp for STK (format: YYYYMMDDHHmmss) in EAT (UTC+3)
        # Render servers are UTC, so we add 3 hours to match Kenya time
        eat_time = datetime.utcnow() + timedelta(hours=3)
        timestamp = eat_time.strftime('%Y%m%d%H%M%S')

        # Generate password: Base64(ShortCode + Passkey + Timestamp)
        import base64
        import re
        
        # Clean alphanumeric reference and description (Max 12 / 13 chars)
        def clean_str(s, length):
            if not s: return ""
            return re.sub(r'[^a-zA-Z0-9]', '', str(s))[:length]

        clean_reference = clean_str(reference_id, 12)
        clean_description = clean_str(description, 13) or "Payment"

        password_string = f"{self.short_code}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()

        payload = {
            "BusinessShortCode": self.short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": self.transaction_type,
            "Amount": int(amount),  # Must be integer
            "PartyA": phone_number,
            "PartyB": self.till_number,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": clean_reference,  # Max 12 chars
            "TransactionDesc": clean_description   # Max 13 chars
        }

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            session = create_session_with_retries(max_retries=3, backoff_factor=0.5)
            response = session.post(
                self.stk_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"STK push initiated: {data}")

            return {
                'success': data.get('ResponseCode') == '0',
                'checkout_request_id': data.get('CheckoutRequestID'),
                'response_code': data.get('ResponseCode'),
                'message': data.get('ResponseDescription', 'STK push initiated')
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"STK push failed after retries: {str(e)}", exc_info=True)
            return {
                'success': False,
                'checkout_request_id': None,
                'response_code': 'STK_FAILED',
                'message': f'STK push error: {str(e)}'
            }

    def query_transaction_status(self, checkout_request_id):
        """
        Query the result of an STK push request
        
        Args:
            checkout_request_id: CheckoutRequestID from initiate_stk_push response
            
        Returns:
            {
                'success': bool,
                'result_code': str,
                'result_desc': str,
                'checkout_request_id': str
            }
        """
        token = self.authenticate()
        if not token:
            return {
                'success': False,
                'result_code': 'AUTH_FAILED',
                'result_desc': 'Authentication failed'
            }

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        import base64
        password_string = f"{self.short_code}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()

        payload = {
            "BusinessShortCode": self.short_code,
            "CheckoutRequestID": checkout_request_id,
            "Password": password,
            "Timestamp": timestamp
        }

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.query_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Query result: {data}")

            return {
                'success': data.get('ResultCode') == '0',
                'result_code': data.get('ResultCode'),
                'result_desc': data.get('ResultDesc'),
                'checkout_request_id': data.get('CheckoutRequestID')
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Query failed: {str(e)}")
            return {
                'success': False,
                'result_code': 'QUERY_FAILED',
                'result_desc': str(e)
            }


def get_mpesa_client():
    """Factory function to get M-Pesa client instance"""
    return MpesaClient()
