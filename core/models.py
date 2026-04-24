# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
 
 
class AwardMilesPackage(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    harga_paket = models.DecimalField(max_digits=15, decimal_places=2)
    jumlah_award_miles = models.IntegerField()
 
    class Meta:
        managed = False
        db_table = 'award_miles_package'
 
 
class Bandara(models.Model):
    iata_code = models.CharField(primary_key=True, max_length=3)
    nama = models.CharField(max_length=100)
    kota = models.CharField(max_length=100)
    negara = models.CharField(max_length=100)
 
    class Meta:
        managed = False
        db_table = 'bandara'
 
 
class Penyedia(models.Model):
    class Meta:
        managed = False
        db_table = 'penyedia'
 
 
class Tier(models.Model):
    id_tier = models.CharField(primary_key=True, max_length=10)
    nama = models.CharField(max_length=50)
    minimal_frekuensi_terbang = models.IntegerField()
    minimal_tier_miles = models.IntegerField()
 
    class Meta:
        managed = False
        db_table = 'tier'
 
 
class Pengguna(models.Model):
    email = models.CharField(primary_key=True, max_length=100)
    password = models.CharField(max_length=255)
    salutation = models.CharField(max_length=10)
    first_mid_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=5)
    mobile_number = models.CharField(max_length=20)
    tanggal_lahir = models.DateField()
    kewarganegaraan = models.CharField(max_length=50)
 
    class Meta:
        managed = False
        db_table = 'pengguna'
 
 
class Member(models.Model):
    email = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='email', primary_key=True)
    nomor_member = models.CharField(unique=True, max_length=20)
    tanggal_bergabung = models.DateField()
    id_tier = models.ForeignKey(Tier, models.DO_NOTHING, db_column='id_tier')
    award_miles = models.IntegerField(blank=True, null=True)
    total_miles = models.IntegerField(blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'member'
 
 
class Maskapai(models.Model):
    kode_maskapai = models.CharField(primary_key=True, max_length=10)
    nama_maskapai = models.CharField(max_length=100)
    id_penyedia = models.OneToOneField(Penyedia, models.DO_NOTHING, db_column='id_penyedia')
 
    class Meta:
        managed = False
        db_table = 'maskapai'
 
 
class Staf(models.Model):
    email = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='email', primary_key=True)
    id_staf = models.CharField(unique=True, max_length=20)
    kode_maskapai = models.ForeignKey(Maskapai, models.DO_NOTHING, db_column='kode_maskapai')
 
    class Meta:
        managed = False
        db_table = 'staf'
 
 
class Identitas(models.Model):
    nomor = models.CharField(primary_key=True, max_length=50)
    email_member = models.ForeignKey(Member, models.DO_NOTHING, db_column='email_member')
    tanggal_habis = models.DateField()
    tanggal_terbit = models.DateField()
    negara_penerbit = models.CharField(max_length=50)
    jenis = models.CharField(max_length=30)
 
    class Meta:
        managed = False
        db_table = 'identitas'
 
 
class Hadiah(models.Model):
    kode_hadiah = models.CharField(primary_key=True, max_length=20)
    nama = models.CharField(max_length=100)
    miles = models.IntegerField()
    deskripsi = models.TextField(blank=True, null=True)
    valid_start_date = models.DateField()
    program_end = models.DateField()
    id_penyedia = models.ForeignKey(Penyedia, models.DO_NOTHING, db_column='id_penyedia')
 
    class Meta:
        managed = False
        db_table = 'hadiah'
 
 
class MemberAwardMilesPackage(models.Model):
    id_award_miles_package = models.ForeignKey(AwardMilesPackage, models.DO_NOTHING, db_column='id_award_miles_package')
    email_member = models.ForeignKey(Member, models.DO_NOTHING, db_column='email_member')
    timestamp = models.DateTimeField()
 
    class Meta:
        managed = False
        db_table = 'member_award_miles_package'
        unique_together = (('id_award_miles_package', 'email_member', 'timestamp'),)
 
 
class Mitra(models.Model):
    email_mitra = models.CharField(primary_key=True, max_length=100)
    id_penyedia = models.OneToOneField(Penyedia, models.DO_NOTHING, db_column='id_penyedia')
    nama_mitra = models.CharField(max_length=100)
    tanggal_kerja_sama = models.DateField()
 
    class Meta:
        managed = False
        db_table = 'mitra'
 
 
class Redeem(models.Model):
    email_member = models.ForeignKey(Member, models.DO_NOTHING, db_column='email_member')
    kode_hadiah = models.ForeignKey(Hadiah, models.DO_NOTHING, db_column='kode_hadiah')
    timestamp = models.DateTimeField()
 
    class Meta:
        managed = False
        db_table = 'redeem'
        unique_together = (('email_member', 'kode_hadiah', 'timestamp'),)
 
 
class ClaimMissingMiles(models.Model):
    email_member = models.ForeignKey(Member, models.DO_NOTHING, db_column='email_member')
    email_staf = models.ForeignKey(Staf, models.DO_NOTHING, db_column='email_staf', blank=True, null=True)
    maskapai = models.ForeignKey(Maskapai, models.DO_NOTHING, db_column='maskapai')
    bandara_asal = models.ForeignKey(Bandara, models.DO_NOTHING, db_column='bandara_asal')
    bandara_tujuan = models.ForeignKey(Bandara, models.DO_NOTHING, db_column='bandara_tujuan', related_name='claim_tujuan_set')
    tanggal_penerbangan = models.DateField()
    flight_number = models.CharField(max_length=10)
    nomor_tiket = models.CharField(max_length=20)
    kelas_kabin = models.CharField(max_length=20)
    pnr = models.CharField(max_length=10)
    status_penerimaan = models.CharField(max_length=20)
    timestamp = models.DateTimeField()
 
    class Meta:
        managed = False
        db_table = 'claim_missing_miles'
        unique_together = (('email_member', 'flight_number', 'tanggal_penerbangan', 'nomor_tiket'),)
 
 
class Transfer(models.Model):
    email_member_1 = models.ForeignKey(Member, models.DO_NOTHING, db_column='email_member_1')
    email_member_2 = models.ForeignKey(Member, models.DO_NOTHING, db_column='email_member_2', related_name='transfer_penerima_set')
    timestamp = models.DateTimeField()
    jumlah = models.IntegerField()
    catatan = models.CharField(max_length=255, blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'transfer'
        unique_together = (('email_member_1', 'email_member_2', 'timestamp'),)
 