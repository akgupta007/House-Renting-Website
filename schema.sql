CREATE TABLE users (
id SERIAL PRIMARY KEY NOT NULL, username TEXT NOT NULL UNIQUE, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.00
);

ALTER SEQUENCE user_id_seq RESTART WITH 0;

CREATE TABLE transaction_log (
transaction_id text PRIMARY KEY NOT NULL, customer_id int NOT NULL,price NUMERIC NOT NULL,type TEXT NOT NULL, time timestamp with time zone ,flat_no integer, user_id integer
);

CREATE TABLE reset (
id int NOT NULL , sq CHARACTER(1) NOT NULL , sa VARCHAR(20) NOT NULL , FOREIGN KEY(id) REFERENCES users(id)
);


CREATE TABLE public.districts
(
    district integer NOT NULL,
    name character varying(20) COLLATE pg_catalog."default",
    subdistricts integer,
    university character varying(100) COLLATE pg_catalog."default",
    density integer,
    popular character varying(100) COLLATE pg_catalog."default",
    CONSTRAINT districts_pkey PRIMARY KEY (district)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.districts
    OWNER to postgres;


CREATE TABLE public.housing
(
    link character varying(50) COLLATE pg_catalog."default",
    flat_no integer NOT NULL,
    price numeric(10,5),
    square numeric(10,5),
    living integer,
    drawing integer,
    kitchen integer,
    bedroom integer,
    buildingtype double precision,
    constructiontime integer,
    renovationcondition integer,
    buildingstructure integer,
    elevator integer,
    fiveyearsproperty integer,
    subway integer,
    district integer,
    communityaverage integer,
    sale integer,
    owner integer,
    image_url text,
    CONSTRAINT housing_pkey PRIMARY KEY (flat_no),
    CONSTRAINT "Foreign Key" FOREIGN KEY (district)
        REFERENCES public.districts (district) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.housing
    OWNER to postgres;

-- Index: fki_Foreign Key

-- DROP INDEX public."fki_Foreign Key";

CREATE INDEX "fki_Foreign Key"
    ON public.housing USING btree
    (district)
    TABLESPACE pg_default;

CREATE TABLE rent_house(flat_no integer NOT NULL PRIMARY KEY, 
tenant_id integer,
rent_status integer,
CONSTRAINT "fkey" FOREIGN KEY (flat_no)
REFERENCES public.housing (flat_no));


create view tenant as select housing.flat_no,name,price,square,kitchen,living,bedroom,sale,rent_status,'tenant'as ownership,tenant_id as id from housing,districts,rent_house where rent_house.flat_no = housing.flat_no and housing.district = districts.district;

create view house_owner as select flat_no,name,price,square,kitchen,living,bedroom,sale, (case when flat_no in (select rent_house.flat_no from rent_house) Then 1 else 0 end) as rent_status, 'owner' as ownership,owner as id from housing,districts where housing.district = districts.district;

create or replace function update_time() returns trigger as $$
begin
update transaction_log set time = current_timestamp where transaction_id = new.transaction_id;
return new;
end;
$$ language plpgsql;

create trigger update_transaction after insert on transaction_log for each row execute procedure update_time();

\COPY public.districts FROM 'E:\courses\sem6\col362_DBMS\project\districts.csv' DELIMITER ',' CSV HEADER;
\COPY public.housing FROM 'E:\courses\sem6\col362_DBMS\project\housing_.csv' DELIMITER ',' CSV HEADER;