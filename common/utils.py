
import decimal
import datetime
import logging
import re

from functools import wraps


_logger = logging.getLogger(__name__)


def calculate_router_status(offline_devices, dormant_devices, online_devices):
    """calculates the overall router status
    based on the total number of offline, dormant and online devices.
    """
    good_color = "#228B22"
    fair_color = "#FFD700"
    poor_color = "#FFA500"
    critical_color = "#FF0000"

    total_devices = offline_devices + dormant_devices + online_devices
    if total_devices <= 0:
        return ("None", "#808080")

    # Calculate percentages (safe to divide now since total_devices > 0)
    offline_percent = (offline_devices / total_devices) * 100
    dormant_percent = (dormant_devices / total_devices) * 100
    online_percent = (online_devices / total_devices) * 100

    # Check for critical scenarios (all or most offline)
    if offline_percent == 100:
        return ("Critical", "#FF0000")  # Red
    elif offline_percent > 50 or (offline_percent > 0 and dormant_percent > 0):
        return ("Critical", "#FF0000")  # Red

    # Determine if 'few' applies to offline and dormant
    few_offline = 10 <= offline_percent <= 25
    few_dormant = 10 <= dormant_percent <= 25

    # Categorize based on percentages (matching the new table)
    if online_percent == 100:
        return ("Good", "#228B22")  # Green
    elif online_percent > 50:
        if few_dormant:
            return ("Good", "#228B22")  # Green
        else:
            return ("Good", "#228B22")  # Green
    else:
        if few_offline:
            return ("Fair", "#FFD700")  # Yellow
        elif few_dormant:
            return ("Fair", "#FFD700")  # Yellow
        else:
            return ("Poor", "#FFA500")  # Orange


def to_float(n):
    """
    Converts the input to a floating-point number.

    Parameters:
        n (str or int): The input to convert to a float.

    Returns:
        float: The converted floating-point number. If the conversion fails, returns 0.0.
    """
    try:
        return float(n)
    except ValueError:
        pass
    return 0.0


def ddm_to_decimal(latitude, ns, longitude, ew):
    """
    A function to convert degrees, minutes, and seconds to decimal degrees.

    Parameters:
        degrees (str or int): The degrees part of the coordinate.
        direction (str): The direction (N, S, E, or W) of the coordinate.

    Returns:
        float: The converted decimal degree value.
    """

    def dms_to_dd(degrees, direction):
        dd = to_float(degrees)
        if direction.upper() == "S" or direction.upper() == "W":
            dd = dd * -1
        return dd

    lat = dms_to_dd(latitude, ns)
    lng = dms_to_dd(longitude, ew)

    return {"lat": lat, "lng": lng}


def convert_to_json_safe(obj):
    if type(obj) is decimal.Decimal:
        return float(obj)
    if type(obj) is datetime.datetime:
        return obj.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    return obj


def log_errors(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        return_val = None
        try:
            return_val = func(*args, **kwargs)
        except Exception as e:
            _logger.error(e, exc_info=True)
        return return_val
    return inner_func




def camel_to_snake(text):
  """Converts camelCase text to snake_case.

  Args:
      text: The camelCase string to convert.

  Returns:
      The snake_case version of the input string.
  """

  # Regex Pattern Explanation:
  # - Look for any uppercase letter A-Z: [A-Z]
  # - That is preceded by a lowercase letter or number: (?<=[a-z0-9])
  # - OR any uppercase letter A-Z that is not at the start: (?!^)[A-Z]
  # - Followed by a lowercase letter: (?=[a-z])

  return re.sub(r'(?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z])', r'_\g', text).lower()
