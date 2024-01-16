#!/usr/bin/env python3

import datetime
import json
import logging
import os
import os.path
import sys
import argparse
from typing import Optional

_CACHE_PATH = os.path.expandvars("${HOME}/.aws/gccache")

log = logging.getLogger(__name__)
logging.basicConfig(level="INFO")


def cache_path(profile_name: str) -> str:
	return _CACHE_PATH + profile_name


def try_get_creds(profile: str) -> Optional[bytes]:
	try:
		with open(cache_path(profile), "rb") as f:
			credsRaw = f.read()
		creds: dict = json.loads(credsRaw)
		expStr = creds.get("Expiration") or None
		if expStr is None:
			log.info("couldn't read expiration")
			return None
		exp = datetime.datetime.fromisoformat(expStr)
		if exp < datetime.datetime.now(tz=datetime.timezone.utc):
			log.info("credentials expired")
			return None
		return credsRaw
	except FileNotFoundError:
		log.info("creds don't exist yet")
		return None
	except Exception as e:
		log.error("error getting cached credentials:", exc_info=e)
		return None


def get_or_refresh(profile_name: str) -> bytes:
	credsRaw = try_get_creds(profile_name)
	if credsRaw is not None:
		return credsRaw
	print("please paste your credentials", file=sys.stderr)
	credsRaw = sys.stdin.buffer.read()
	with open(cache_path(profile_name), "wb") as f:
		f.write(credsRaw)
	return credsRaw


def main() -> None:
	parser = argparse.ArgumentParser("aws-scrape-creds")
	parser.add_argument("--profile", required=True)
	args = parser.parse_args()
	profile_name: str = args.profile

	credsRaw = get_or_refresh(profile_name=profile_name)
	sys.stdout.buffer.write(credsRaw)


if __name__ == "__main__":
	main()
