.PHONY: up down api web test migrate seed install

# Thin delegator — the real project (and its own Makefile) lives in peacock-one/.
up down api web test migrate seed install:
	$(MAKE) -C peacock-one $@
