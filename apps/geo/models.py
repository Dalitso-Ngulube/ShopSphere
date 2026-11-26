from django.db import models

from apps.common.models import TimeStampedModel


class Province(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class District(TimeStampedModel):
    province = models.ForeignKey(
        Province,
        on_delete=models.PROTECT,
        related_name="districts",
    )
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["province", "name"],
                name="uq_district_province_name",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.province.name})"
