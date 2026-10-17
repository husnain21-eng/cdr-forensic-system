# CDR Forensic Investigator System

A secure desktop application for law-enforcement investigators to
analyze Call Detail Records (CDRs), visualize communication networks,
detect anomalies, and generate evidence-grade PDF dossiers.

![Status](https://img.shields.io/badge/status-stable-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## Overview

The system ingests CDR datasets from multiple telecom operators
(CSV, XLSX, XLS), normalizes their varied column formats, and produces:

- **Contact network graphs** with centrality rankings
- **Risk assessments** using a transparent, documented heuristic
- **Anomaly detection** — short calls, night activity, missed-ping patterns
- **Mutual contact analysis** between two target numbers
- **Co-location detection** — moments when two targets were near each other
- **Interactive geo-spatial maps** (Folium + Esri tiles)
- **Watermarked A4 PDF dossiers** with chain-of-custody audit trail

All data is encrypted at rest. Every privileged action is logged with
an HMAC-signed, hash-chained entry in a tamper-evident audit table.

---

## Features

| Feature | Description |
|---|---|
| 🔐 **AES encryption** | Workspace DB encrypted with Fernet; master key in OS keyring |
| 🧂 **PBKDF2 password hashing** | 200,000 iterations of PBKDF2-HMAC-SHA256 |
| 👥 **Role-Based Access Control** | Admin and Junior Analyst roles with enforced permissions |
| 📝 **Hash-chained audit trail** | Blockchain-style log — tampering breaks the chain |
| ⏱ **Auto-lock** | Idle sessions lock after 5 minutes |
| 📊 **Multi-tab dashboard** | 7 analytical views in a single window |
| 🌍 **Interactive maps** | Marker clustering, heatmaps, triangulation radii |
| 📄 **PDF dossiers** | Watermarked, restricted-marked A4 reports |
| 🖨 **Print any tab** | Live preview dialog, print current tab |
| 🎨 **Light/dark themes** | Persistent theme preference |
| 🔤 **Adjustable font size** | 11–22 px, persisted across sessions |
| 🔍 **Advanced filters** | Filter by date/time range and phone number |
| 🚀 **Bulk loading** | Load and combine multiple CDR files |
| 🔄 **Reset session** | Clear all loaded data with a single click |
| 🧠 **Advanced Mathematics** | Markov Chains (Prediction), Spectral Clustering (Community Detection), Z-Scores (Statistics), Haversine (Trigonometry), and Graph Theory (Centrality) |
---

## Architecture