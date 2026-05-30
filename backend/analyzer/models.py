from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Autor(models.Model):
    id_autor = models.AutoField(primary_key=True)
    nume = models.CharField(max_length=30)
    prenume = models.CharField(max_length=25, null=True, blank=True)
    data_nasterii = models.DateField(default='1900-01-01')
    data_deces = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'autor'
        verbose_name_plural = 'Autori'

    def __str__(self):
        return f'{self.nume} {self.prenume or ''}'.strip()

class Carte(models.Model):
    id_carte = models.AutoField(primary_key=True)
    id_autor = models.ForeignKey(Autor, on_delete=models.CASCADE, db_column='id_autor', null=True, blank=True)
    titlu = models.CharField(max_length=255)
    an_aparitie = models.IntegerField(validators=[MinValueValidator(1001), MaxValueValidator(2026)])
    nr_pagini = models.IntegerField(default=0)
    nr_capitole = models.IntegerField(default=1)

    class Meta:
        db_table = 'carte'
        verbose_name_plural = 'Cărți'

    def __str__(self):
        return self.titlu

class Personaj(models.Model):
    GEN_CHOICES = [('Masculin', 'Masculin'), ('Feminin', 'Feminin')]
    TIP_CHOICES = [('Principal', 'Principal'), ('Secundar', 'Secundar'), ('Episodic', 'Episodic'), ('Colectiv', 'Colectiv')]
    id_personaj = models.AutoField(primary_key=True)
    id_carte = models.ForeignKey(Carte, on_delete=models.CASCADE, db_column='id_carte')
    nume = models.CharField(max_length=50)
    gen = models.CharField(max_length=50, choices=GEN_CHOICES, default='Masculin')
    tip_personaj = models.CharField(max_length=30, choices=TIP_CHOICES, default='Secundar')

    class Meta:
        db_table = 'personaj'
        verbose_name_plural = 'Personaje'

    def __str__(self):
        return f'{self.nume} ({self.tip_personaj})'

class Relatie(models.Model):
    id_relatie = models.AutoField(primary_key=True)
    id_personaj1 = models.ForeignKey(Personaj, on_delete=models.CASCADE, db_column='id_personaj1', related_name='relatii_ca_p1')
    id_personaj2 = models.ForeignKey(Personaj, on_delete=models.CASCADE, db_column='id_personaj2', related_name='relatii_ca_p2')
    numar_dialoguri = models.IntegerField(default=1)

    class Meta:
        db_table = 'relatie'
        unique_together = ('id_personaj1', 'id_personaj2')
        verbose_name_plural = 'Relații'

    def clean(self):
        if self.id_personaj1_id and self.id_personaj2_id:
            if self.id_personaj1_id >= self.id_personaj2_id:
                raise ValidationError('id_personaj1 must be strictly less than id_personaj2 to enforce undirected uniqueness.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.id_personaj1.nume} <-> {self.id_personaj2.nume} ({self.numar_dialoguri} dialoguri)'