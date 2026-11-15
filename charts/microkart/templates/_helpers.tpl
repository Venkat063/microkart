{{/* Services to deploy: implemented ones, plus scaffolds when deployScaffolds=true. */}}
{{- define "mk.enabled" -}}
{{- $out := list -}}
{{- range (.Files.Get "services.yaml" | fromYaml).services -}}
{{- if or .implemented $.Values.deployScaffolds -}}{{- $out = append $out . -}}{{- end -}}
{{- end -}}
{{- toJson $out -}}
{{- end -}}

{{- define "mk.labels" -}}
app.kubernetes.io/name: {{ .svc.name }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/part-of: microkart
app.kubernetes.io/managed-by: {{ .root.Release.Service }}
microkart.io/domain: {{ .svc.domain }}
{{- end -}}

{{- define "mk.selector" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/instance: {{ .release }}
{{- end -}}

{{- define "mk.dbname" -}}{{ . | replace "-" "_" }}{{- end -}}
