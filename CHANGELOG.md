# Changelog

All notable changes to this project are documented in this file.

## [0.10.0](https://github.com/derliebemarcus/homeassistant_teltonika_rms/compare/v0.9.12...v0.10.0) (2026-06-28)


### Features

* add tests for DOMAIN and DEFAULT_STATE_INTERVAL constants ([b5612b2](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b5612b2b15fb024095f295454aef86093c798339))
* **tests:** add test for DOMAIN constant to kill mutant ([47ecc4e](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/47ecc4ef0445f15fde4e3a3aad2718571d0797bb))


### Bug Fixes

* add a unit test that keeps the Dependabot exemption narrow and preserves the normal message rules for all other commits ([27cfd1f](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/27cfd1f53c20222d5dfd402d40ba4307091523b7))
* add pip-index-url to security audit action ([634b121](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/634b12114c8d7eb7a42a1b3bbccdc906278de16e))
* add repository-level icon compatibility for HACS ([bc397bd](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/bc397bd4b4e9c6b976651f67d3769ee0c0455848))
* add unit coverage for missing lines to surpass 97.8% coverage ([ecd76d8](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/ecd76d8a8254d33951aa19f6fbec08c9c2c6be59))
* adjust coverage threshold and finalize quality gates ([42bec91](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/42bec918d03a5334922fe8b5fda8100778a6bab6))
* align device inventory with current RMS schema ([#79](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/79)) ([00763c7](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/00763c7a292fa9ab07034281dd5a1c8bca57654a))
* align local and remote OSV scanning and resolve leaks ([ec43d22](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/ec43d229bc8e211802a6b8dc553798f987dccee8))
* align release workflow check names ([#69](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/69)) ([4de35e2](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4de35e2d16aea3323f5af586f0f04083f7fb37ab))
* applied Ruff formatting and manifest version increment ([4c4ec34](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4c4ec34914fc88693ae70d60a77b4c6fa5122d15))
* audited component for Home Assistant 2026.4.4 compliance ([4c4ec34](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4c4ec34914fc88693ae70d60a77b4c6fa5122d15))
* automate dependency updates and align runtime pin ([#70](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/70)) ([e3f5038](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/e3f5038f3dd1532c323ec700077e5cc276476882))
* avoid blocking setup on optional port refreshes ([2c18cd5](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/2c18cd5599844bb21995b77a8a7f67b8155205f7))
* build(deps): bump cryptography from 46.0.5 to 46.0.6 ([#12](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/12)) ([17d4412](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/17d44124b6b22843b384b64f14962ec574bf462d))
* build(deps): bump pyjwt from 2.10.1 to 2.12.0 ([#11](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/11)) ([19d01d0](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/19d01d06c90e77bdb96bf1d3d340dd47020853d1))
* bump mypy from 1.20.2 to 2.1.0 ([#75](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/75)) ([d181d8b](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/d181d8baa1e37cf8f42bca7617fac874c15f7ea4))
* check_coverage_threshold automatically bumps minimum coverage to prevent regressions ([ecd76d8](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/ecd76d8a8254d33951aa19f6fbec08c9c2c6be59))
* **ci:** align boto dependency pins ([b54ee4b](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b54ee4b647569b075976f5398835f0d8be839871))
* **ci:** align locked boto dependency pins ([a0b9fca](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/a0b9fca06ecb7e665624eb8235aedcaa4883641c))
* **ci:** harden Jenkins workspace and report stages ([7f52614](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/7f5261494fcf8e492c18a3aab96225f36c2dd223))
* **ci:** normalize Jenkins workspace permissions before parallel stages ([e74df4a](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/e74df4a57c917c0f52cc8c43a6c10ca0e1420847))
* **ci:** remove conflicting locked boto transitives ([1bc7a4e](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/1bc7a4ed7697c9213a9b9eca27b52ba0b909cdf1))
* **ci:** remove conflicting transitive boto pins ([1c8832d](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/1c8832d532d55ff842a1e667fcd226d56892fe60))
* **ci:** repair development requirements ([434b98d](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/434b98dde95d56c9d34c904cb226771948f4c6d0))
* **ci:** repair locked requirements conflict markers ([6a8ba81](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/6a8ba815d2a9c28760400e047e1f4cca2bf6aa8a))
* consolidate CI and coverage logic ([181825f](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/181825fc7f5b96194c4680ac55a698161fe598d1))
* consolidate vulnerability management in osv-scanner.toml ([c60d1be](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/c60d1bec89f25a8fd0449b25518393e67d92938b))
* correct chained patch statement syntax in HA conftest ([fc9cb6f](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/fc9cb6fbf700203d58eb34c7a050e21329244c87))
* correct Home Assistant conftest mocks and imports ([5b6db88](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/5b6db8866e0c16234d0e222423848e2037ef94fd))
* correct OAuth2 reauthentication flow ([bc397bd](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/bc397bd4b4e9c6b976651f67d3769ee0c0455848))
* correct path for mutmut artifact upload ([9328c6a](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/9328c6ab2955255513a2fa33f3dbde0820f0b1ac))
* correctly configure pytest-cov to generate test contexts for mutmut ([ea21254](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/ea212540e999c92c18533d99ae154895832a7e05))
* correctly execute python module commands inside the local venv ([1fb2931](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/1fb2931e1a7bab7246906cbbf5f3ef9ec54fe472))
* decouple port link state from switch administration state ([b3989a5](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b3989a5692b870f6a654fd562d82f31c24250240))
* degrade ethernet port scans gracefully when device_actions:read is missing ([a51180a](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/a51180ac11a77848b5d9f1b70976506ab19eba0d))
* **deps:** restore lockfile consistency on main ([#78](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/78)) ([2780482](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/2780482b68734d445aa23bbcb2d6351e9435ee09))
* document the release-workflow lint correction in the release notes for the 0.8.3 patch release ([cc18204](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/cc18204204e0f490c2f39704f7063147a1a8afcf))
* empty commit to clear ci cache ([59cd441](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/59cd4413661d7aa876299bb385d5ccc0f266d718))
* ensure NIL ports are filtered before generating fallback switch ports ([22c06ee](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/22c06eeee24316b48299b3007abc787f212a84b5))
* fallback switch port logic and poe detection ([f7561b9](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/f7561b9454a231b1ce511669a0bfbdff97c81b47))
* finalize hassfest compliance for HACS inclusion ([1bbea1c](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/1bbea1ca5cd29a263256e68a8c996df023030159))
* fix hacs.json by removing disallowed domains key ([b10e0c1](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b10e0c193c565e72639c3f29f4211574d90c4988))
* force the generation of all physical ports (port1-8 and sfp1-2) for switch devices so they do not disappear when disconnected. ([0d65513](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/0d655137c6b2063967cbde66c6e47ea36aa87eaa))
* format code with ruff to fix ci pipeline ([b1c898e](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b1c898e3dfe93fb7b0944163f0a33fcfe2aeff6c))
* format imports with ruff ([c44cea5](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/c44cea5654ee9c6dd280d13b833287275568fdc1))
* generate pytest coverage with dynamic contexts for mutmut ([adef40b](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/adef40bc253210a061d48cabbb32452860fa98c8))
* handle empty string port identification securely ([ecd76d8](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/ecd76d8a8254d33951aa19f6fbec08c9c2c6be59))
* handle missing before commit in github actions on force push ([bdcd235](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/bdcd2355fad55c9b8b34b3e991a32d645d6fb6e6))
* ignore CVE-2026-39892 in pip-audit as it is pinned by HomeAssistant ([706bc86](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/706bc86be95475383f82d49da94704f0e609103b))
* ignore unpatched April 2026 vulnerabilities and fix workflow permissions ([15c4f5f](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/15c4f5f329d06af44289150ff7bb8f64b911c673))
* ignore upstream pyopenssl cves in security gates ([b54eaa4](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b54eaa4112e690bf99589df064b70f1e37f31fcc))
* ignored pytest CVE in pre-commit for stability ([4c4ec34](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4c4ec34914fc88693ae70d60a77b4c6fa5122d15))
* improve pre-commit hooks and timestamp parsing ([4c1d342](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4c1d342dd0e78aca7dbbe5cf9fa74df207aa11b4))
* improve switch and sensor generation logic ([f7561b9](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/f7561b9454a231b1ce511669a0bfbdff97c81b47))
* keep the bypass case-sensitive so only uppercase prefix forms skip the normal commit-message rules ([1576cc5](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/1576cc518a6eb6201f13e64b15a529ff9f616e01))
* make mutation testing a precondition for releases ([8c75f69](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/8c75f694ca102ff7baefd06474400e2eceaffd28))
* make the release workflow tag/version comparison pass shellcheck and actionlint ([55ed0b2](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/55ed0b2690c8f0991b84b2dd21f2e2f63deeba0c))
* move brand assets to integration directory for HACS validation ([7a2c995](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/7a2c995ebbf2edf2490a18ee5521aa318801bf26))
* mutmut 3 shadow directory import errors and test selection ([a9ac434](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/a9ac4340c7b3fdae398a3167b8b5c95a94495714))
* normalize README license and coverage badges ([bc397bd](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/bc397bd4b4e9c6b976651f67d3769ee0c0455848))
* pin orjson and PyJWT to secure versions ([d0a28a0](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/d0a28a0060c13536304551cfdd1f41bac5a609a4))
* populate switch entities when port configuration endpoint fails but port scan succeeds ([60b71c7](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/60b71c7815345a299e85df40cebadcdbcd265230))
* prepare Teltonika RMS for HACS default submission ([b16ac17](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b16ac17f29f5286363037b17e733338bba5e7162))
* preserve default scopes when generating endpoint matrix to authorize PAT requests ([2744cd4](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/2744cd4df0cebe346150c127c84934b318147b47))
* prevent one device from blocking port configuration for all others ([7476e58](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/7476e58471c9b688395f341173eaa544260f9874))
* relax commit message validation to allow optional scopes and common prefixes ([706bc86](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/706bc86be95475383f82d49da94704f0e609103b))
* remediate SonarQube quality gate compliance issues ([b9c0ddb](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b9c0ddbe4552bdcff4d65e68848492ed1c4b332f))
* remove accidentally committed temp_input directory ([fd05fbe](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/fd05fbeeea00bd0673e2b85f1adb2b5b6b3471fa))
* request and document device_remote_access:read for ethernet port scan sensors ([febef4d](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/febef4db3780febd062dfdececac05e35bf47177))
* resolve bugs in PoE/Ethernet payloads and add missing wireless clients_count ([72348cd](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/72348cd13c62e827b1f5cac88e91272e09062058))
* resolve duplicate switch port link sensors and ensure visibility of disconnected switch ports ([0d65513](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/0d655137c6b2063967cbde66c6e47ea36aa87eaa))
* resolve GitHub build failures and prepare beta release ([706bc86](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/706bc86be95475383f82d49da94704f0e609103b))
* resolve HACS validation errors and restructure repository ([b10e0c1](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b10e0c193c565e72639c3f29f4211574d90c4988))
* resolve OSV workflow syntax and sync pip-compile headers ([bfbe254](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/bfbe2548b66993cdbacb18a63708183ca490d3ba))
* resolve RuntimeWarnings in tests by correcting AsyncMock usage for non-coroutines ([706bc86](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/706bc86be95475383f82d49da94704f0e609103b))
* resolve SonarQube cognitive complexity and code hygiene issues ([0642b28](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/0642b283fff708dce9e3565187741a0692afca30))
* resolved config flow test mocking and executor job resolution ([4c4ec34](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4c4ec34914fc88693ae70d60a77b4c6fa5122d15))
* resolved mypy type errors in core and test suite ([4c4ec34](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4c4ec34914fc88693ae70d60a77b4c6fa5122d15))
* Resolved test suite breakages and unawaited coroutine warnings in flow runtime tests. ([3a0bd96](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/3a0bd96090497b781d524b9fa41b1744ccf87563))
* restore coverage margin after 0.8.0 release ([8914254](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/8914254fd2a23824602743f6e694a56f255fee2e))
* restore missing PoE and firmware update entities ([bc0bff9](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/bc0bff9782a64ab6e3291f3a425bccbc2b0a0492))
* restore strict test coverage and enforce minimums ([ecd76d8](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/ecd76d8a8254d33951aa19f6fbec08c9c2c6be59))
* restore valid dependency pins and security suppressions ([b431203](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b431203994d5df75548bdbe30f887fd73dcc2894))
* revert binary sensor to beta9 and remove admin port switches ([848af4f](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/848af4fe2d48cfc67fa457a656fdbd4bb82e1dd4))
* revert orjson and PyJWT pins due to conflicts with upstream Home Assistant core dependencies ([906b13e](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/906b13ea1eff2dd2ed9996045a7d96bf4a8c7e72))
* reverted invalid pre-push hook flag ([c60d1be](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/c60d1bec89f25a8fd0449b25518393e67d92938b))
* robust project root discovery for mutation testing ([d10ca39](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/d10ca392554b92632f1797f54312e20c27f6f77a))
* **security:** correct gitleaks ignore fingerprints ([c114447](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/c11444714d1446796fe26bba1aaf94454355bc56))
* ship python-socketio 5.14.0 to remove the current socketio vulnerability from the published integration ([cc18204](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/cc18204204e0f490c2f39704f7063147a1a8afcf))
* ship python-socketio 5.16.1 in the published integration so the released package matches the merged security updates on main ([9dae053](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/9dae053c59d6f650c77169d481709f32514ac7bd))
* show ethernet switches for TSW and SWM devices ([0965fcc](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/0965fcc178d405c3aba6d6828ea8fc48839a3681))
* sonar coverage report download path ([dd8634e](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/dd8634eba1c7e7295ee1ad3a762b071adb20c018))
* sort manifest.json keys correctly ([cc084b0](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/cc084b06c3f661be4c51c4a9c420ee56fc5d3806))
* stabilize coverage and update for HA 2026.4.4 ([4c4ec34](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4c4ec34914fc88693ae70d60a77b4c6fa5122d15))
* stabilize pipeline, sync lockfiles with pins, suppress environmental vulns, and recover code coverage ([f0aefb2](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/f0aefb2da1750451b2694e33505fe8b30768e0d2))
* standardize Makefile engine detection and sync security audit ignore list ([b2dcfaf](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/b2dcfaf4f74e016ed483ad1cf92cf504fd4526e7))
* synchronize lockfile and resolve remaining CI failures ([0b43096](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/0b430964e8a56a2c602c77e438adeb7504d2e9d6))
* **tests:** enable mutmut debug logging and fix sys.path ([2d5eeaf](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/2d5eeaff107c2cb775177f625533d78457a9c036))
* tighten typing and test coverage so the new static-analysis gate passes cleanly ([70ea255](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/70ea255fbdaffd83c55ee744f8fe2640c666f4ff))
* update hooks for pytest CVE stabilization ([d1e6ce9](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/d1e6ce94c4efc7543443ae3ddefbfbd714afb3c4))
* update PATH in workflows to include standard directories ([01454bb](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/01454bbff8894ef41c5b653fd045f2ed32b59dfb))
* update resolves an issue where switch devices (TSW/SWM) generated duplicate port entities. ([0d65513](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/0d655137c6b2063967cbde66c6e47ea36aa87eaa))
* update tests after removing async_setup and homeassistant key ([6472c5a](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/6472c5a7e795b33a389d77db6f3200d6d7265ab8))
* update workflow and script paths for manifest.json after restructure ([dd1cac7](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/dd1cac74eda20c75b88a8d06c9b2b6a05bf16d0f))
* update workflow syntax to satisfy GitHub Action parsers ([3869dd3](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/3869dd3b7f27c5afe03d0275583dff13457df762))
* updated pre-push hook to ignore pytest GHSA-6w46-j5rx-g56g ([d1e6ce9](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/d1e6ce94c4efc7543443ae3ddefbfbd714afb3c4))
* upgrade python-socketio to 5.14.0 in runtime and development dependencies to satisfy the security gate ([55ed0b2](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/55ed0b2690c8f0991b84b2dd21f2e2f63deeba0c))
* use state from port scan payload for switches if missing from configurations ([60b71c7](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/60b71c7815345a299e85df40cebadcdbcd265230))
* waive CVE-2025-67221 and CVE-2026-32597 vulnerabilities from pip-audit ([bb83f5a](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/bb83f5ab6dd2b7866b8fcfbc1f9d51026e47a897))
* When a device (like TAP200) returned ConfigEntryAuthFailed because it lacked support for the configurator endpoint, the entire loop was aborted, preventing TSW/SWM devices from receiving their port configs. ([7476e58](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/7476e58471c9b688395f341173eaa544260f9874))

## [0.9.12](https://github.com/derliebemarcus/homeassistant_teltonika_rms/compare/v0.9.11...v0.9.12) (2026-06-27)


### Bug Fixes

* align device inventory with current RMS schema ([#79](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/79)) ([00763c7](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/00763c7a292fa9ab07034281dd5a1c8bca57654a))
* align release workflow check names ([#69](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/69)) ([4de35e2](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/4de35e2d16aea3323f5af586f0f04083f7fb37ab))
* automate dependency updates and align runtime pin ([#70](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/70)) ([e3f5038](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/e3f5038f3dd1532c323ec700077e5cc276476882))
* bump mypy from 1.20.2 to 2.1.0 ([#75](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/75)) ([d181d8b](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/d181d8baa1e37cf8f42bca7617fac874c15f7ea4))
* **deps:** restore lockfile consistency on main ([#78](https://github.com/derliebemarcus/homeassistant_teltonika_rms/issues/78)) ([2780482](https://github.com/derliebemarcus/homeassistant_teltonika_rms/commit/2780482b68734d445aa23bbcb2d6351e9435ee09))

## 0.9.11 - 2026-06-24

### New Features

- None.

### Improvements

- Prepared the repository metadata for submission to the default HACS store.
- Removed the incorrect Switzerland-only HACS availability restriction.

### Changes

- Updated the manifest documentation, issue tracker, and code owner for the renamed repository.

### Bugfixes

- None.

## 0.9.11-beta.3 - 2026-04-30

### New Features

- None.

### Improvements

- Achieved 98% code coverage (exceeding 97.1% quality gate).
- Audited and confirmed compatibility with Home Assistant 2026.4.4.
- Hardened the test suite with strict mypy typing for all core and test modules.
- Reverted pytest and pytest-asyncio to stable versions (8.4.2 / 0.23.8) to resolve dependency collisions with Home Assistant core.

### Changes

- None.

### Bugfixes

- Fixed configuration flow test failures by correcting mock behavior for executor jobs and data-entry flows.
- Resolved type mismatch errors in the sensor and coordinator logic identified by static analysis.
- Fixed lockfile synchronization issues during local pre-commit checks.

## 0.9.11-beta.2 - 2026-04-09

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Relaxed commit message validation rules to allow optional scopes (e.g., `build(deps):`) and more common prefixes.
- Resolved `RuntimeWarning` issues in tests where non-coroutine Home Assistant methods were being mocked as `AsyncMock` or awaited.

## 0.9.11-beta.1 - 2026-04-02

### New Features

- Added Pydantic v2 runtime contract validation for RMS device-list, device-detail, and device-state payloads so upstream API schema drift fails with controlled integration errors.
- Added Syrupy snapshot coverage for diagnostics output to lock the JSON structure exposed to Home Assistant support tooling.

### Improvements

- Enforced mypy strict mode across the integration code and test suite, including the Home Assistant-heavy mock/runtime tests.
- Activated Ruff PEP257 docstring enforcement and kept the public diagnostic sensor classes documented.
- Pinned the developer dependency set with `pip-tools`, added a checked-in `requirements.txt` lockfile, and added CI drift detection for the lockfile.
- Added automatic virtualenv maintenance so activating `.venv` or `.venv-test` upgrades `pip`.
- Hardened the local pre-push gate so OSV-Scanner is mandatory before pushes.

### Changes

- Updated the developer README to document contract tests, snapshot tests, lockfile maintenance, strict static analysis, and automatic virtualenv pip maintenance.
- Updated release automation so beta tags publish as prereleases while production tags are explicitly marked as the latest release.

### Bugfixes

- Fixed API contract-drift handling to raise `RmsApiError` instead of continuing with unsafe best-effort parsing.
- Resolved strict-typing issues in HA runtime tests, mock fixtures, and config-entry test scaffolding.
- Fixed the lockfile consistency workflow to compile with Python 3.14, matching the checked-in lockfile.

## 0.9.10 - 2026-03-24

### New Features

- None.

### Improvements

- Added native light and dark mode support for the Teltonika brand logo in the repository README using HTML `<picture>` elements.

### Changes

- None.

### Bugfixes

- None.

## 0.9.9 - 2026-03-24

### New Features

- None.

### Improvements

- Restructured the README to include a comprehensive Table of Contents.
- Updated the Teltonika tracking links and references in the README documentation.

### Changes

- None.

### Bugfixes

- None.

## 0.9.8 - 2026-03-24

### New Features

- None.

### Improvements

- Added an explicit `dark_icon.png` to ensure HACS renders the integration brand logo correctly when Home Assistant is in dark mode.

### Changes

- None.

### Bugfixes

- None.

## 0.9.7 - 2026-03-24

### New Features

- None.

### Improvements

- Updated the integration README.
- Added a new brand logo.

### Changes

- None.

### Bugfixes

- None.

## 0.9.6 - 2026-03-24

### New Features

- None.

### Improvements

- Updated the integration brand icon.
- Added `.gitleaksignore` and ignored `temp_input` directory to resolve GitHub Actions secret-scan failures.

### Changes

- None.

### Bugfixes

- Fixed GitHub Actions quality workflow crashing on force pushes due to missing 'before' commit in `github.event.before`.

## 0.9.5 - 2026-03-19

### New Features

- Added Home Assistant Hassfest validation to automated checks.

### Improvements

- Sorted `manifest.json` keys according to Home Assistant requirements.
- Cleaned up `__init__.py` by removing redundant `async_setup` and its associated `hassfest` warning.

### Changes

- None.

### Bugfixes

- Fixed `hassfest` validation errors to meet HACS inclusion requirements.

## 0.9.4 - 2026-03-19

### New Features

- None.

### Improvements

- Finalized HACS validation by moving brand assets into the integration directory.
- Updated GitHub Action workflows and internal tools to support the new `custom_components/teltonika_rms/` repository structure.

### Changes

- None.

### Bugfixes

- Fixed broken paths in GitHub Action workflows that prevented automated releases.

## 0.9.3 - 2026-03-19

### New Features

- Added repository topics to satisfy HACS requirements.
- Restructured repository to follow standard `custom_components/teltonika_rms/` layout.

### Improvements

- Fixed `hacs.json` by removing the disallowed `domains` key.
- Updated all local tools and tests to support the new directory structure.

### Changes

- None.

### Bugfixes

- None.

## 0.9.2 - 2026-03-19

### New Features

- Added GitHub Action for automated HACS validation to prepare for default repository inclusion.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- None.

## 0.9.1 - 2026-03-19

### New Features

- None.

### Improvements

- Updated the README to ensure its contents accurately match the integration's capabilities.

### Changes

- None.

### Bugfixes

- None.

## 0.9.0 - 2026-03-19

### New Features

- None.

### Improvements

- Stable release of the 0.9.0 beta series.

### Changes

- None.

### Bugfixes

- None.

## 0.9.0-beta16 - 2026-03-19

### New Features

- None.

### Improvements

- Reached Home Assistant "Platinum" Quality Scale level by explicitly defining parallel updates and declaring `quality_scale` in manifest.

### Changes

- None.

### Bugfixes

- Fixed an issue where switch devices generated a duplicate `switch_port1` link sensor instead of merging it into `port1`.
- Ensured link sensors are correctly generated for all switch device ports even if the ports are completely disconnected and not explicitly returned by the API's PoE configuration endpoint.

## 0.9.0-beta15 - 2026-03-17

### New Features

- None.

### Improvements

- Increased test coverage suite from 97.81% to 97.83% and covered remaining edge cases relating to missing or malformed `PoE (W)` floats and string formatting logic.

### Changes

- None.

### Bugfixes

- Fixed an issue causing Coveralls to report a `-0.02%` coverage regression in PRs. Missing paths and newly introduced PoE conditions have been completely backfilled with automated unit tests.

## 0.9.0-beta14 - 2026-03-17

### New Features

- None.

### Improvements

- Increased test coverage to >97.8% and automated the pre-commit script to continuously bump the coverage floor upon success, ensuring coverage can only remain stagnant or improve.

### Changes

- None.

### Bugfixes

- Fixed a bug where a port explicitly labeled with an empty string `""` from the configuration payload was silently dropped when detecting missing ports for auto-generation.

## 0.9.0-beta13 - 2026-03-17

### New Features

- Restored the exact `binary_sensor` and auto-generation naming logic from `v0.9.0-beta9` based on user feedback.
- Restricted the creation of PoE Power sensors and PoE Switches strictly to supported device series (`OTD`, `SWM`, `TSW`, and `RUT` excluding `RUTX` and `RUTM`).

### Improvements

- Expanded the pre-commit configuration to completely replicate all remote GitHub Actions security and quality checks locally, ensuring maximum test parity before committing.

### Changes

- Removed regular administrative port `switch` entities per user feedback.

### Bugfixes

- Fixed PoE power and state extraction missing due to case-sensitivity and unhandled `PoE (W)` properties for certain switch models.

## 0.9.0-beta12 - 2026-03-17

### New Features

- None.

### Improvements

- None.

### Changes

- Ignored upstream pyOpenSSL vulnerabilities `CVE-2026-27448` and `CVE-2026-27459` in the security gates to allow the CI pipeline to pass.

### Bugfixes

- None.

## 0.9.0-beta11 - 2026-03-17

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Hotfix for TSW and SWM switch ports failing to auto-generate link sensors and switches when the RMS configuration API returns a single empty "NIL" port instead of a truly empty list.

## 0.9.0-beta10 - 2026-03-16

### New Features

- Added PoE power sensor (`PoE (W)`) for Ethernet ports that expose PoE capabilities.
- Firmware updates now check strictly against the latest stable firmware instead of the absolute latest firmware.
- The integration now intelligently auto-populates `switch_port1` through `switch_port8` and `sfp1` through `sfp2` for unlisted disconnected ports on TSW and SWM models to ensure link sensors and switches appear.

### Improvements

- Modified the configuration error on PoE and Port switches to clarify that failing to turn a switch on/off might be due to the device model not supporting remote RMS port administration, rather than only missing scopes.

### Changes

- Ports named `NIL` are now completely ignored and will not generate binary sensors or switch entities.

### Bugfixes

- Fixed disconnected ports for TSW and SWM devices not generating link sensors because they were incorrectly auto-generated with the `port` prefix instead of the `switch_port` prefix.
- Fixed Ethernet port switches showing as "Off" instead of "On" when their administrative state was inaccessible through the API.

## 0.9.0-beta9 - 2026-03-16

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Fixed disconnected port links and switches completely missing from Home Assistant for TSW and SWM devices. The integration now intelligently auto-populates `port1` to `port8` and `sfp1` to `sfp2` when they are unlisted by the Teltonika RMS API payload.

## 0.9.0-beta8 - 2026-03-16

### New Features

- Added a new binary sensor for each ethernet port to indicate the active link status.

### Improvements

- Changed default polling intervals for device state (300 seconds) and inventory (3600 seconds).
- Made options for device tags, device status filters, and OpenAPI YAML path completely optional.
- Renamed the generic "Serial" sensor friendly name to "Serial Number".

### Changes

- Removed the "Used Ethernet Ports" and "Used Ethernet Port Names" aggregate sensors in favor of the new individual per-port link binary sensors.
- If a device lacks the `device_configurations:write` scope or doesn't support the configurator endpoint, attempting to toggle a port switch will surface a clear error and no longer fall back to the physical link state.

### Bugfixes

- Fixed TSW switch entities from falsely reporting an `On` state when the configuration API failed. Switch states now default to `Unknown` (`None`) when their administrative "enabled" state is inaccessible.

## 0.9.0-beta7 - 2026-03-16

### New Features

- None.

### Improvements

- Added port_scan synchronization to switch.py so that ethernet switches appear correctly via scan data when device configuration APIs are inaccessible.

### Changes

- None.

### Bugfixes

- Fixed an issue where the correct switch states were not shown if a device returned missing configuration endpoints but succeeded in port-scan data.

## 0.9.0-beta6 - 2026-03-16

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Fixed an issue where port switches were completely ignored for all devices if any single device lacked permission or support for the configurator API endpoint.

## 0.9.0-beta5 - 2026-03-16

### New Features

- None.

### Improvements

- Added debug logging for switch creation and port discovery.

### Changes

- None.

### Bugfixes

- Fixed ethernet switches not appearing for TSW and SWM devices.

## 0.9.0-beta4 - 2026-03-16

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Fixed formatting issues that caused the previous release pipeline to fail.

## 0.9.0-beta3 - 2026-03-16

### New Features

- Added support for switching ethernet port states on and off.
- Added support for changing PoE capability.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- None.


## 0.9.0-beta2 - 2026-03-15

### New Features

- Automatically update floating tags ('stable' or 'beta') based on the published release type.

### Improvements

- Clarified supported devices in the README.

### Changes

- None.

### Bugfixes

- None.

## 0.9.0-beta1 - 2026-03-15

### New Features

- Published a new beta version.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- None.

## 0.9.0-beta0 - 2026-03-14

### New Features

- Introduced beta versions (pre-releases) in addition to stable releases.

### Improvements

- Updated documentation to clarify that while the plugin aims to support all Teltonika devices, it has been specifically tested and validated with the RUTX50, TAP200, and TSW202.

### Changes

- None.

### Bugfixes

- None.

## 0.8.8 - 2026-03-14

### New Features

- None.

### Improvements

- Temperature sensor values are now exposed as `float` type and assigned the `MEASUREMENT` state class for better graph tracking.
- SIM slot values are now exposed natively as integer.

### Changes

- None.

### Bugfixes

- Fixed wireless `clients_count` missing for Access Points (TAP200) and Routers (RUTX50) by parsing the newly supported `/devices/{device_id}/wireless` endpoint.
- Fixed an issue where `used_ethernet_ports` and `used_ethernet_port_names` did not populate for certain switches like the TSW202 due to an unhandled API wrapper payload format.
- Fixed PoE switches failing to populate for devices like the TSW202.

## 0.8.7 - 2026-03-14

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Reverted the dependency pinning of `orjson` and `PyJWT` introduced in `0.8.6` because they directly conflicted with the strict dependencies of Home Assistant 2026.3.0 and 2026.3.1. These vulnerability alerts are upstream within Home Assistant Core and will be fixed when the next core version ships them.

## 0.8.6 - 2026-03-14

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Fixed security vulnerabilities by pinning `orjson>=3.11.6` (CVE-2025-67221) and `PyJWT>=2.12.0` (CVE-2026-32597) in the integration dependencies.

## 0.8.5 - 2026-03-14

### New Features

- None.

### Improvements

- Modified the endpoint matrix generator tool to correctly preserve default endpoint scopes when parsing OpenAPI definitions that use `BearerAuth` without explicitly redefining scope sets per path.

### Changes

- None.

### Bugfixes

- Fixed the `endpoint_matrix_frozen.json` scope generation so that PAT users with `devices:read` grants are correctly authorized when using generated matrix files.

## 0.8.4 - 2026-03-14

### New Features

- None.

### Improvements

- Shipped the runtime `python-socketio` dependency at `5.16.1`, so installations now include the latest Dependabot-delivered security and maintenance updates instead of staying on the older `5.14.0` floor.
- Updated QA workflow dependencies alongside the release so repository checks run on the newer `pytest-cov`, `actionlint`, `actions/github-script`, and `actions/upload-artifact` revisions already merged on `main`.

### Changes

- Published a follow-up patch release after the Dependabot merges so the released integration version matches the security-relevant dependency state on `main`.

### Bugfixes

- Fixed the release packaging gap where merged security updates on `main` had not yet been rolled into a tagged Home Assistant release.

## 0.8.3 - 2026-03-14

### New Features

- None.

### Improvements

- Upgraded the bundled `python-socketio` dependency to `5.14.0`, removing a known vulnerability and bringing the shipped integration dependency set back into compliance with the repository security gates.

### Changes

- Tightened the release workflow shell comparison so `actionlint` and ShellCheck can validate release publishing end to end without false-positive script failures.

### Bugfixes

- Fixed the GitHub Actions release workflow lint failure caused by an inline tag comparison pattern that ShellCheck flagged as invalid.
- Fixed the dependency-audit failure by shipping a non-vulnerable `python-socketio` version in both runtime and development dependency manifests.

## 0.8.2 - 2026-03-13

### New Features

- None.

### Improvements

- Firmware update entities now tolerate more RMS firmware metadata shapes, including string-based `current`, `latest`, and `stable` values returned by some devices.

### Changes

- Update entity discovery now also reacts to state coordinator refreshes, not only inventory refreshes.
- RMS status-channel completion detection now accepts both `status: completed` and `response_state: completed`.

### Bugfixes

- Fixed PoE switch discovery when RMS configurator status payloads finish with `completed` instead of `success`, so PoE switch entities can be created after the background port-configuration refresh finishes.
- Fixed missing firmware update entities for devices that expose firmware metadata in alternative RMS shapes that were previously not normalized into the integration model.

## 0.8.1 - 2026-03-13

### New Features

- None.

### Improvements

- Optional Ethernet port scan and PoE port-configuration refreshes now start in the background after setup, so the core integration becomes available immediately even when RMS status channels are slow or the socket falls back to HTTP polling.

### Changes

- Initialized optional port-scan and port-configuration coordinators with empty data so entity setup stays safe before the first background refresh completes.

### Bugfixes

- Fixed a setup-path regression in `0.8.0` where Home Assistant could remain stuck on `Loading next step for Teltonika RMS` while waiting for optional port-scan or port-configuration first refreshes to finish.

## 0.8.0 - 2026-03-13

### New Features

- Added PoE `switch` entities for configurable switch ports, so supported Teltonika switch ports can now be turned on and off directly from Home Assistant.

### Improvements

- PoE switches are created only for ports where RMS actually exposes a `poe_enable` setting, so non-PoE ports such as SFP uplinks do not create misleading entities.
- PoE state is now read from the RMS configurator port configuration endpoint, which keeps Home Assistant aligned with the actual current device configuration.

### Changes

- Expanded the requested OAuth2 scopes to include:
  - `device_configurations:read`
  - `device_configurations:write`
- Added a dedicated low-frequency port-configuration coordinator alongside the existing Ethernet port-scan coordinator.
- Updated README scope guidance and feature list to document PoE switches and their required permissions.

### Bugfixes

- None.

## 0.7.2 - 2026-03-13

### New Features

- None.

### Improvements

- OAuth2 and PAT scope guidance now matches the actual RMS permission needed for Ethernet port scan sensors.

### Changes

- Added `device_remote_access:read` to the requested OAuth scope set for Teltonika RMS.
- Updated runtime warnings and README scope instructions so Ethernet port scan sensors point to `device_remote_access:read` instead of the incorrect `device_actions:read`.

### Bugfixes

- Fixed the Ethernet port scan permission guidance after live validation showed that `device_actions:read` alone still returns `403` for `/devices/{id}/port-scan/`.

## 0.7.1 - 2026-03-13

### New Features

- None.

### Improvements

- Missing `device_actions:read` permission for the optional Ethernet port scan no longer blocks the whole integration from starting after upgrade.

### Changes

- None.

### Bugfixes

- Fixed startup behavior so Ethernet port scan refresh degrades gracefully to `no Ethernet entities` when the scope is missing, instead of repeatedly forcing Home Assistant into reconnect/reauth behavior.

## 0.7.0 - 2026-03-13

### New Features

- Added a read-only firmware `update` entity per device so Home Assistant now shows the installed firmware alongside the latest version RMS reports for that device.
- Added Ethernet diagnostics sensors that expose how many Ethernet ports are currently in use and which named ports have active downstream devices.

### Improvements

- Reused RMS inventory firmware metadata directly for update availability, so firmware visibility works without extra file-catalog setup.
- Added a dedicated low-frequency port-scan coordinator so Ethernet visibility is available without materially increasing the RMS request budget.

### Changes

- Extended the integration setup and runtime bundle with an `update` platform and an Ethernet port-scan coordinator.
- Updated README scope guidance so `device_actions:read` is called out explicitly for Ethernet port scan sensors.

### Bugfixes

- None.

## 0.6.1 - 2026-03-13

### New Features

- None.

### Improvements

- Changed router uptime presentation from raw seconds to days, making long-running devices easier to read directly in Home Assistant.

### Changes

- None.

### Bugfixes

- Fixed the reboot action to use the correct RMS endpoint `/devices/actions` instead of the invalid versioned path.

## 0.6.0 - 2026-03-13

### New Features

- Added new optional RMS sensors that are created only when the API actually provides the value:
  - clients count
  - router uptime
  - temperature
  - signal strength
  - WAN state
  - connection state
  - connection type
  - SIM slot
- Added a per-device reboot button so supported devices can be restarted directly from Home Assistant.
- Added representative RMS contract fixtures derived from the compiled API schema to validate payload handling against more realistic examples.

### Improvements

- Expanded diagnostics output with auth mode, aggregate-state availability, and monthly request estimate to make support cases easier to debug.
- Added repository quality gates for commit-message format and release-note structure so project rules are enforced in CI, not only by local hooks.
- Added issue templates, a pull-request template, and maintainer contribution guidance to make incoming changes and bug reports more actionable.

### Changes

- Updated README to document the new RMS sensors and clarify that they are only exposed when RMS provides the underlying value.
- Updated OAuth2/PAT scope documentation to include `device_actions:write` for the reboot button.
- Added repository-level governance tooling:
  - `tools/check_commit_messages.py`
  - `tools/check_release_notes.py`
  - `.github/workflows/quality.yml`

### Bugfixes

- Fixed OAuth2 reauthentication flow so it correctly restarts implementation selection instead of calling a non-existent superclass reauth method.

## 0.5.2 - 2026-03-13

### New Features

- None.

### Improvements

- Added repository-level `icon.png` compatibility branding alongside `brand/icon.png` so HACS can resolve the integration icon more reliably.
- Raised automated test coverage to 97%, giving stronger regression protection for config flow, coordinators, API fallback paths, and repository metadata.
- Added enforcement for structured release notes so GitHub releases consistently highlight product impact first and maintenance/testing items afterwards.

### Changes

- Standardized README badges so all top-level badges use a consistent `for-the-badge` height and styling.
- Enforced categorized commit-message bodies through a `commit-msg` hook:
  - `add:`
  - `change:`
  - `deprecate:`
  - `remove:`
  - `fix:`

### Bugfixes

- Fixed OAuth2 reauthentication to restart implementation selection correctly instead of calling a non-existent superclass reauth method.
- Replaced the unstable dynamic license badge with a stable MIT badge so the repository page no longer shows `repo not found`.

## 0.5.1 - 2026-03-13

### New Features

- None.

### Improvements

- Increased automated test coverage to 94% across the integration codebase, improving regression protection for authentication, coordinator updates, and status-channel handling.
- Expanded runtime coverage for RMS API retries, pagination, aggregate-state fallback, and channel resolution so remote-device state handling is validated more thoroughly.
- Expanded unit coverage for endpoint-matrix parsing and device normalization helpers, reducing the chance of API-schema or payload-shape regressions.

### Changes

- Kept the Coveralls workflow aligned with the current HA/runtime dependency floor so published coverage stays current and comparable across releases.

### Bugfixes

- None.

## 0.5.0 - 2026-03-13

- Added README badges for HACS, GitHub releases, license, and downloads.
- Expanded OAuth setup documentation:
  - `my.home-assistant.io` link requirement is now documented explicitly.
  - RMS OAuth redirect URL is documented as `https://my.home-assistant.io/redirect/oauth`.
  - Post-credential setup steps in Home Assistant are documented more clearly.
- Simplified integration branding assets to a single local icon:
  - kept `brand/icon.png`
  - removed unused logo and dark-variant files
- Raised the minimum supported Home Assistant version to `2026.3.0`:
  - aligns with local brand icon support for custom integrations
  - mirrored in both `manifest.json` and `hacs.json`
- Added a metadata consistency test to keep `manifest.json` and `hacs.json` aligned.

## 0.4.0 - 2026-03-11

- Updated integration metadata documentation URL:
  - Home Assistant "help/documentation" link now points to the project repository:
    - `https://github.com/derliebemarcus/teltonika_rms`

## 0.3.1 - 2026-03-11

- Refined test execution split:
  - Added `tests/unit/` for pure unit tests that run without Home Assistant dependencies.
  - Added `tests/ha/` for Home Assistant-dependent tests.
- Updated `pre-commit` hook behavior:
  - Without `homeassistant` installed: runs all unit tests.
  - With `homeassistant` installed: runs unit + HA test suites.
  - Keeps `--maxfail=0` and blocks commit only after all selected tests completed.
- Added HA-test marker configuration in `pytest.ini`.
- Refactored integration module imports in `__init__.py` to avoid importing heavy HA/runtime dependencies at module import time, improving testability outside HA.

## 0.3.0 - 2026-03-11

- Added versioned repository Git hooks (`.githooks`):
  - `pre-commit` runs all tests, prints per-test name/duration/result, and blocks commit on failures.
  - `pre-push` enforces an existing release tag `v<manifest.version>`.
- Added tooling scripts:
  - `tools/install_git_hooks.sh`
  - `tools/print_pytest_summary.py`
  - `tools/create_version_tag.sh`
- Extended location normalization to detect more coordinate formats (`lat/lng`, `lon`, GeoJSON coordinate arrays, coordinate strings).
- Device tracker now exposes explicit location attributes:
  - `location_detail`
  - `coordinates`
  - `google_maps_url`

## 0.2.0 - 2026-03-11

- Added dual authentication modes:
  - OAuth2 (Authorization Code + PKCE)
  - Personal Access Token (PAT)
- Added PAT reauthentication flow.
- Added diagnostics endpoint with token redaction.
- Added HACS metadata and Python-specific `.gitignore`.
- Switched `last_seen` from `datetime` entity to `sensor` timestamp entity.
- Ensured device tracker entities are only created when valid coordinates exist.
- Added and localized translation files for EU languages and additional requested languages.
- Expanded README:
  - Installation via HACS and manual copy
  - Configuration flow
  - Detailed credential setup steps for OAuth2 and PAT
- Added endpoint matrix tooling and regenerated frozen matrix support.
- Added issue tracker URL in manifest and bumped integration version to `0.2.0`.

## 0.1.0 - 2026-03-11

- Initial custom integration scaffold for Teltonika RMS.
- OAuth2 config flow, API client, coordinators, and basic entities.
- Request budget estimation and channel-status fallback support.
