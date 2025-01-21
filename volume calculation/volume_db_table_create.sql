CREATE TABLE public.petrol_demo
(
    gid integer NOT NULL DEFAULT nextval('petrol_demo_gid_seq'::regclass),
    gridcode bigint,
    cap smallint,
    parca smallint,
    uzunluk numeric,
    hacim numeric,
    islem smallint,
    orig_fid integer,
    hesap numeric,
    geom geometry(MultiLineString,4326),
    CONSTRAINT petrol_demo_pkey PRIMARY KEY (gid)
)
