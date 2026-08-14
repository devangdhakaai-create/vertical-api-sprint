# Stage 1: Build stage
FROM python:3.14-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final stage
FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port $PORT


# Line-by-line samjho:

# FROM python:3.13-slim AS builder = ek lightweight Python base image se shuru karo, ise "builder" naam do (multi-stage build ka pehla stage)
# WORKDIR /app = container ke andar /app folder banao, wahi kaam karo
# COPY requirements.txt . = pehle sirf requirements file copy karo (poora code nahi) — ye Docker caching ka trick hai, agar code change ho but requirements na ho, to ye step dobara nahi chalega, build fast hoga
# RUN pip install --user ... = packages install karo
# Doosra FROM python:3.13-slim = ek fresh, chhota image shuru karo final container ke liye (builder stage ka extra build-tools waala weight nahi chahiye)
# COPY --from=builder ... = sirf installed packages copy karo builder stage se, poora build environment nahi
# COPY . . = ab apna poora code copy karo
# EXPOSE 8000 = batao ki container port 8000 use karega
# CMD [...] = container start hote hi ye command chalegi (0.0.0.0 zaroori hai — localhost nahi, warna container ke bahar se access nahi hoga)