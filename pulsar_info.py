from astropy.coordinates import EarthLocation
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import EarthLocation, Angle
import datetime, time
import numpy as np

#GBD observatory

longitude = 77.437547;  # degrees
latitude = 13.603839;  # degrees
height = 713;  # meters

observing_location = EarthLocation(lat=latitude*u.deg, lon=longitude*u.deg)

def get_all_time(): 
    IST = str(np.datetime64(datetime.datetime.now()))
    UTC = datetime.datetime.now(datetime.UTC)
    Astro_fmt = Time(IST, format='isot', scale='utc')
    Julian_day = Astro_fmt.jd
    Modified_Julian_day = Astro_fmt.mjd
    
    observing_time = Time(UTC, scale='utc', location=observing_location)
    LST = observing_time.sidereal_time('mean')
    #LST.to_string(unit=u.hour, sep=':')
    
    return LST, IST

def RA(k):
    from psrqpy import QueryATNF
    query = QueryATNF(params=['F0'])
    psrs = query.get_pulsars()
    # Get Local Sidereal Time
    lst_now, ist_now = get_all_time()

    #print(lst_now)

    # Example: Target LST from somewhere (maybe from schedule)
    target_lst_str = psrs[k].RAJ  # example: 2:15 AM LST
    target_lst = Angle(target_lst_str, unit='hour')

    # Compute difference between LSTs (handle wraparound correctly)
    lst_diff = (target_lst - lst_now).wrap_at(24 * lst_now.unit)

    #print(f"Difference: {lst_diff}")
    #print(f"Difference in hours: {lst_diff.hour:.2f} hrs")

    # Add the LST difference to current IST time to estimate target IST time
    # Convert LST difference in hours to seconds
    seconds_to_wait = lst_diff.hour * 3600

    #print(seconds_to_wait)

    # Current IST as datetime object
    current_ist_dt = datetime.datetime.now()

    # Future IST time when target LST occurs
    target_ist_dt = current_ist_dt + datetime.timedelta(seconds=seconds_to_wait)

    #print(f"Estimated IST when LST reaches {target_lst_str}: {target_ist_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    return target_ist_dt, seconds_to_wait
