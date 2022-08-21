create type "user_role" as enum ("regular", "admin")

create table "user" (
  id        serial    primary key,
  type      user_role not null,
  is_active boolean   not null default false
);

create table "product" (
  id          serial  primary key,
  title       text    not null,
  description text    not null,
  price_rub   decimal not null
);

create table "payment_account" (
  id          serial  primary key,
  user_id     integer not null,
  balance_rub decimal not null default 0,
  foreign key (user_id) references "user" (id)
      on update cascade on delete cascade
);

create table "transaction" (
  id serial primary key,
  payment_account_id integer not null,
  amount_rub decimal not null,
  foreign key (payment_account_id) references "payment_account" (id)
      on update cascade on delete cascade
);