# Nordic nRF5 SDK CMake generator
Generate CMake for Nordic nRF5 SDK with additional functionalities

Idea and basic implementation taken from [_Jumperr-labs's_ `nrf5-sdk-clion`](https://github.com/Jumperr-labs/nrf5-sdk-clion) and [_Polidea's_ `cmake-nRF5x`](https://github.com/Polidea/cmake-nRF5x).

At first custom Makefile parsing was almost implemented but then [pymake](https://github.com/mozilla/pymake) project ([forked](https://github.com/bojanpotocnik/pymake) to enable relative imports) was used for parsing.
