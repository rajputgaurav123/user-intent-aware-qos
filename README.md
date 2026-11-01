# User-Intent-Aware Adaptive QoS Engine

## 1. Project Overview

This project is a prototype that allocates bandwidth according to user intent and estimated network congestion.

A user can select:
- Video Call
- Gaming
- Streaming
- Download

The policy engine adjusts bandwidth allocation across three traffic classes:
- Interactive
- Streaming
- Bulk

The goal is to prioritize latency-sensitive activities while preserving some bandwidth for other traffic.

## 2. How It Works

1. The user selects an intent.
2. The measurement module estimates throughput, latency, latency variation, and packet loss.
3. A congestion heuristic estimates the network condition.
4. A Random Forest model predicts a traffic class and provides a confidence score.
5. The policy engine uses the user's explicit intent and congestion level to calculate bandwidth shares.
6. Linux Traffic Control (tc) applies the policy to an isolated virtual interface.
7. iperf3 measures throughput in controlled experiments.

Important: The current ML prediction is reported as supporting information. It does not override the explicit user intent.

## 3. Architecture

User Intent
    |
    v
Network Measurements ---> Congestion Estimator
    |                            |
    v                            v
Random Forest Prediction ---> Policy Engine
                                  |
                                  v
                         Linux Traffic Control
                                  |
                                  v
                         Isolated Virtual Link
                                  |
                                  v
                          iperf3 Measurements

## 4. Technology Stack

- Python
- scikit-learn Random Forest
- pandas and joblib
- Linux Traffic Control (tc)
- HTB queueing discipline
- iperf3
- WSL2 Ubuntu
- Virtual Ethernet interface pair and network namespace

## 5. Experimental Setup

The prototype uses an isolated virtual network:
- Host-side interface: veth-test
- Namespace: qos-test
- Host-side IP: 10.10.0.1
- Namespace IP: 10.10.0.2
- Configured root link rate: 20 Mbps
- Interactive test port: TCP 5201
- Bulk test port: TCP 5202

The tests do not change the real Internet interface.

## 6. Preliminary Results

Simultaneous iperf3 tests, approximately 15 seconds per flow:

| Configuration | Interactive receiver | Bulk receiver |
|---|---:|---:|
| Equal-share baseline | 6.35 Mbps | 6.33 Mbps |
| Intent-aware run 1 | 14.0 Mbps | 0.894 Mbps |
| Intent-aware repeat | 14.4 Mbps | 0.948 Mbps |

In these runs, interactive throughput increased while bulk throughput decreased. This demonstrates a bandwidth-allocation trade-off under the tested conditions.

These are preliminary results from a small number of runs. More repetitions and controlled latency/jitter measurements are needed before making broader performance claims.

## 7. Machine Learning

The current Random Forest classifier uses these features:
- Throughput
- Latency
- Jitter or latency variation
- Packet loss

The training dataset is synthetic, with three classes: interactive, streaming, and bulk.

Synthetic data supports reproducible development, but performance on synthetic data does not establish real-world traffic-classification accuracy. The current model has not been validated on a representative real-world dataset.

The current classifier predicts a traffic class from aggregate metrics; it does not identify individual packets or inspect encrypted payloads.

## 8. Tests and Validation

Policy unit tests:
- 16 policy tests passed in the recorded test runs.
- Tested all four intents across four congestion levels.
- Checked that allocations total 100% and each class retains at least 5%.

Network experiment:
- Confirmed connectivity between the virtual endpoints.
- Ran simultaneous iperf3 traffic on ports 5201 and 5202.
- Observed Linux traffic-control class counters.
- Repeated the intent-aware throughput test.

## 9. Limitations

- The classifier is trained on synthetic data.
- The current traffic-class prediction is not validated real-world classification.
- Port-based test mapping is a simplified demonstration, not general application identification.
- External Internet measurements do not directly measure the isolated virtual link's capacity.
- The experiment has limited repetitions.
- Interactive throughput gains do not, by themselves, prove lower latency or jitter.
- IPv4 isolated-network testing has been demonstrated; IPv6 behavior requires separate validation.
- The current prototype is experimental and does not modify real Internet traffic.

## 10. Reproducibility

Prerequisites:
- Python and project virtual environment
- Required Python dependencies
- Linux/WSL2 environment with iproute2 and iperf3
- Permissions to configure network namespaces and traffic control

Run the policy tests:

    cd ~/adaptive-qos
    python test_policy.py

Run the interactive prototype:

    python integrated_qos.py

The isolated virtual network and iperf3 servers must be configured and running before repeating the throughput experiment. Refer to the project scripts and verify the current interface and class configuration before each run.

## 11. Future Improvements

- Collect labeled traffic measurements from reproducible experiments.
- Compare ML classification against a deterministic baseline.
- Repeat experiments and report averages and variability.
- Measure latency, jitter, packet loss, and fairness under simultaneous load.
- Add capacity estimation and congestion-adaptation tests.
- Improve application/flow identification and IPv6 validation.
- Add automated setup, cleanup, rollback, and experiment reporting.

## 12. Conclusion

This prototype demonstrates user-intent-driven bandwidth allocation on an isolated virtual network using Linux traffic control. Preliminary experiments show that the selected interactive flow can receive more throughput at the expense of bulk traffic. Further validation is required to establish latency benefits, classification reliability, and performance under broader conditions.

<!-- FINAL-EXPERIMENT-RESULTS-START -->
## Final experiment results

Packaged on: 2026-10-28T22:42:22

Combined machine-readable results: `final_experiment_results.json`

### Result files included
- `scenario1_fixed_results.json`
- `scenario1_results.json`
- `scenario2_results.json`
- `scenario2_simultaneous_results.json`
- `scenario3_gaming_streaming_results.json`

### Experiment notes
- Scenario 1 examines interactive/video-call traffic alongside a bulk download.
- Scenario 2 compares configured shaping profiles under a 100 Mbps baseline and a 20 Mbps cap.
- Scenario 3 compares gaming UDP traffic with three streaming TCP flows.
- See the JSON files for the measurements actually recorded; missing measurements are not inferred.
- The reported experiments are controlled shaping demonstrations, not proof of a production-ready controller.

### Limitations
- Experiments use a controlled Linux HTB traffic-shaping setup.
- Synthetic or simulated traffic is not equivalent to real application traffic.
- Scenario 2's sequential throughput figures must not be summed as concurrent throughput.
- Results from a single run are preliminary; repeat trials are needed.
- These tests do not independently prove automatic real-WAN capacity detection.

<!-- FINAL-EXPERIMENT-RESULTS-END -->

## Network Policy Controller

The Network Policy Controller coordinates user-intent selection, network monitoring, congestion estimation, and QoS policy application.

### Workflow
1. Accepts the user's preferred intent: Video Call, Gaming, Streaming, or Download.
2. Reads the configured link capacity.
3. Measures incoming (RX) and outgoing (TX) traffic.
4. Calculates TX utilization and determines congestion level.
5. Calls the Policy Engine to calculate bandwidth allocation.
6. Applies the allocation using Linux Traffic Control (`tc`).

The controller is designed for the isolated `veth-test` interface.

**Implementation note:** The current controller script requires syntax and indentation corrections and further testing before it can be considered fully functional.

## Link Capacity Estimator

The `capacity_estimator.py` module reads the configured network rate from Linux Traffic Control qdisc information.

### Working Principle
- Reads qdisc information using the `tc` command.
- Searches for a Token Bucket Filter (TBF) configuration.
- Extracts its configured rate.
- Converts the rate into Mbps.

**Limitation:** This estimates a configured shaping rate, not actual internet bandwidth. The current implementation specifically searches for TBF and may not detect capacity when the interface uses HTB.

## Traffic Load Estimator

The `traffic_load_estimator.py` module measures network traffic using Linux interface byte counters.

### Working Principle
1. Reads initial RX and TX byte counters.
2. Waits for a measurement duration (default: 5 seconds).
3. Reads the counters again.
4. Calculates transferred bytes.
5. Converts the measured traffic rate into Mbps.

### Outputs
- RX throughput (Mbps): Incoming traffic rate.
- TX throughput (Mbps): Outgoing traffic rate.

**Limitation:** These are aggregate interface-level measurements, not individual application throughput measurements.

## Congestion Monitor

The `congestion_simulator.py` module monitors network utilization using configured link capacity and measured traffic load.

### Working Principle
- Reads configured link capacity.
- Measures RX and TX traffic.
- Calculates TX utilization:

  `TX Utilization (%) = (TX Mbps / Link Capacity Mbps) × 100`

- Marks congestion as detected when TX utilization reaches or exceeds 90%.

**Limitation:** This module monitors congestion; it does not independently generate traffic or create network congestion. It is a basic congestion monitor, not a complete network impairment simulator.

## Additional Module Implementation Status

| Module | Current implementation |
|---|---|
| User Intent Selection | Four user-intent options |
| Traffic Classifier | Random Forest model trained on synthetic data |
| Policy Engine | Intent- and congestion-based bandwidth allocation |
| Traffic Load Estimator | RX/TX interface-counter measurement |
| Link Capacity Estimator | TBF qdisc configuration reader |
| Network Policy Controller | Script present; syntax correction and testing required |
| Congestion Monitor | TX utilization-based monitoring |
| QoS Enforcement | Linux HTB traffic shaping |
| Dashboard | Flask-based monitoring and policy interface |

