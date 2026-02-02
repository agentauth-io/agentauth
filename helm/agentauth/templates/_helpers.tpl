{{/*
Expand the name of the chart.
*/}}
{{- define "agentauth.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "agentauth.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "agentauth.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "agentauth.labels" -}}
helm.sh/chart: {{ include "agentauth.chart" . }}
{{ include "agentauth.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "agentauth.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agentauth.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "agentauth.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "agentauth.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "agentauth.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" .Release.Name }}
{{- else }}
{{- .Values.externalPostgresql.host }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port
*/}}
{{- define "agentauth.postgresql.port" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "5432" }}
{{- else }}
{{- .Values.externalPostgresql.port | toString }}
{{- end }}
{{- end }}

{{/*
Redis host
*/}}
{{- define "agentauth.redis.host" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-redis-master" .Release.Name }}
{{- else }}
{{- .Values.externalRedis.host }}
{{- end }}
{{- end }}

{{/*
Redis port
*/}}
{{- define "agentauth.redis.port" -}}
{{- if .Values.redis.enabled }}
{{- printf "6379" }}
{{- else }}
{{- .Values.externalRedis.port | toString }}
{{- end }}
{{- end }}

{{/*
Secret name
*/}}
{{- define "agentauth.secretName" -}}
{{- if .Values.secrets.create }}
{{- include "agentauth.fullname" . }}
{{- else }}
{{- .Values.secrets.existingSecret }}
{{- end }}
{{- end }}
