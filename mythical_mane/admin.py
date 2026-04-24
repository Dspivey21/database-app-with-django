"""
Django admin registrations for the Mythical Mane domain models.

Each ModelAdmin keeps the configuration intentionally simple:
  - list_display:    a handful of the most useful columns at a glance
  - search_fields:   text fields you'd plausibly type into a search box
  - list_filter:     low-cardinality columns (universe, status, etc.)
  - date_hierarchy:  on visit/invoice/payment models with a meaningful date

Foreign keys use raw_id_fields where the related table is large enough that the
default <select> dropdown would be unwieldy.
"""
from django.contrib import admin

from .models import (
    Ability,
    CareNote,
    Diagnosis,
    Employee,
    Invoice,
    LineItem,
    Observation,
    Owner,
    Patient,
    PatientAbility,
    Payment,
    ProcedureDefinition,
    Universe,
    Visit,
    VisitDiagnosis,
    VisitProcedure,
)


@admin.register(Universe)
class UniverseAdmin(admin.ModelAdmin):
    list_display = ("universe_id", "name")
    search_fields = ("name",)


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("owner_id", "name", "universe", "phone", "email")
    list_filter = ("universe",)
    search_fields = ("name", "phone", "email", "address")
    list_select_related = ("universe",)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "name", "color", "dob", "owner", "universe")
    list_filter = ("universe",)
    search_fields = ("name", "color", "owner__name")
    list_select_related = ("owner", "universe")
    date_hierarchy = "dob"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "name", "job_role", "specialty", "hire_date", "email")
    list_filter = ("job_role", "specialty")
    search_fields = ("name", "email", "phone", "specialty")
    date_hierarchy = "hire_date"


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("visit_id", "patient", "vet", "start_at", "end_at", "reason")
    list_filter = ("vet",)
    search_fields = ("reason", "patient__name", "vet__name")
    list_select_related = ("patient", "vet")
    date_hierarchy = "start_at"
    raw_id_fields = ("patient", "vet")


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("diagnosis_id", "name", "code")
    search_fields = ("name", "code", "description")


@admin.register(ProcedureDefinition)
class ProcedureDefinitionAdmin(admin.ModelAdmin):
    list_display = ("procedure_id", "name", "standard_cost")
    search_fields = ("name", "description")


# --- The remaining domain models are registered with light defaults so they're
# visible in the admin even though the assignment only requires the seven above.

@admin.register(Ability)
class AbilityAdmin(admin.ModelAdmin):
    list_display = ("ability_id", "name", "ability_type")
    list_filter = ("ability_type",)
    search_fields = ("name",)


@admin.register(PatientAbility)
class PatientAbilityAdmin(admin.ModelAdmin):
    list_display = ("patient_ability_id", "patient", "ability")
    list_select_related = ("patient", "ability")
    raw_id_fields = ("patient", "ability")


@admin.register(VisitProcedure)
class VisitProcedureAdmin(admin.ModelAdmin):
    list_display = ("visit_procedure_id", "visit", "procedure", "employee", "performed_at")
    date_hierarchy = "performed_at"
    list_select_related = ("visit", "procedure", "employee")
    raw_id_fields = ("visit", "procedure", "employee")


@admin.register(VisitDiagnosis)
class VisitDiagnosisAdmin(admin.ModelAdmin):
    list_display = ("visit_diagnosis_id", "visit", "diagnosis", "employee", "recorded_at")
    date_hierarchy = "recorded_at"
    list_select_related = ("visit", "diagnosis", "employee")
    raw_id_fields = ("visit", "diagnosis", "employee")


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("observation_id", "visit_procedure", "observation_type", "observed_value", "unit")
    list_filter = ("observation_type",)
    search_fields = ("description",)
    raw_id_fields = ("visit_procedure",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_id", "visit", "status", "issue_date", "due_date")
    list_filter = ("status",)
    date_hierarchy = "issue_date"
    raw_id_fields = ("visit",)


@admin.register(LineItem)
class LineItemAdmin(admin.ModelAdmin):
    list_display = ("line_item_id", "invoice", "line_item_type", "visit_procedure")
    list_filter = ("line_item_type",)
    raw_id_fields = ("invoice", "visit_procedure")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "invoice", "payment_date", "amount", "payment_method")
    list_filter = ("payment_method",)
    date_hierarchy = "payment_date"
    raw_id_fields = ("invoice",)


# Mission 7: the Django-owned CareNote model.
@admin.register(CareNote)
class CareNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "short_note", "created_at", "follow_up_date", "resolved")
    list_filter = ("resolved",)
    search_fields = ("note", "patient__name")
    list_select_related = ("patient",)
    date_hierarchy = "created_at"
    raw_id_fields = ("patient",)
    readonly_fields = ("created_at",)

    @admin.display(description="Note", ordering="note")
    def short_note(self, obj):
        return (obj.note[:60] + "...") if len(obj.note) > 60 else obj.note
