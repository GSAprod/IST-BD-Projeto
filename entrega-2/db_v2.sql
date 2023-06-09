drop table if exists customer cascade;
drop table if exists order_ cascade;
drop table if exists sale cascade;
drop table if exists pay cascade;
drop table if exists employee cascade;
drop table if exists process cascade;
drop table if exists department cascade;
drop table if exists workplace cascade;
drop table if exists works cascade;
drop table if exists office cascade;
drop table if exists warehouse cascade;
drop table if exists product cascade;
drop table if exists contains cascade;
drop table if exists supplier cascade;
drop table if exists delivery cascade;

---------------------------------------
-- Table creation
---------------------------------------

CREATE TABLE customer(
    cust_no BIGINT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255),
    phone NUMERIC (9),
    address VARCHAR(255),
    UNIQUE(email)
);
    
CREATE TABLE order_(
    order_no BIGINT PRIMARY KEY,
    cust_no BIGINT NOT NULL,
    date DATE,
    FOREIGN KEY(cust_no) REFERENCES customer
);

CREATE TABLE sale(
    order_no BIGINT PRIMARY KEY,
    FOREIGN KEY(order_no) REFERENCES order_
);


CREATE TABLE pay(
    order_no BIGINT REFERENCES sale,
    cust_no BIGINT REFERENCES customer,
    PRIMARY KEY(order_no)
);

CREATE TABLE employee(
    ssn NUMERIC(11) PRIMARY KEY,
    TIN VARCHAR(9),
    bdate DATE,
    name VARCHAR(100),
    UNIQUE(TIN)
);

CREATE TABLE process(
    ssn NUMERIC(11) REFERENCES employee,
    order_no BIGINT REFERENCES order_,
    PRIMARY KEY(ssn, order_no)
);

CREATE TABLE department(
    name VARCHAR(100),
    PRIMARY KEY(name)
);

CREATE TABLE workplace(
    address VARCHAR(255),
    lat DECIMAL(8, 6),
    long DECIMAL(9, 6),
    PRIMARY KEY(address),
    UNIQUE(lat, long)
);


CREATE TABLE works(
    ssn NUMERIC(11) REFERENCES employee,
    name VARCHAR(100) REFERENCES department,
    address VARCHAR(255) REFERENCES workplace,
    PRIMARY KEY(ssn, name, address)
);
    
CREATE TABLE office(
    address VARCHAR(255) REFERENCES workplace
);

CREATE TABLE warehouse(
    address VARCHAR(255) REFERENCES workplace,
    PRIMARY KEY(address)
);

CREATE TABLE product(
    sku VARCHAR(8) NOT NULL,
    name VARCHAR(100),
    description VARCHAR(255),
    price DECIMAL(10, 2) CHECK (price > 0),
    ean NUMERIC(12),
    PRIMARY KEY(sku)
);

CREATE TABLE contains(
    order_no BIGINT REFERENCES order_,
    sku VARCHAR(8) REFERENCES product,
    qty INTEGER NOT NULL CHECK (qty > 0),
    PRIMARY KEY(order_no, sku)
);

CREATE TABLE supplier(
    TIN VARCHAR(9),
    name VARCHAR(100),
    address VARCHAR(255),
    sku VARCHAR(8) NOT NULL REFERENCES product,
    date DATE,
    PRIMARY KEY(TIN, sku) -- E possivel colocar assim, para que o delivery funcione?
);

CREATE TABLE delivery(
    TIN VARCHAR(9),
    sku VARCHAR(8),
    address VARCHAR(255) REFERENCES warehouse,
    PRIMARY KEY(TIN, sku, address),
    FOREIGN KEY(TIN, sku) REFERENCES supplier(TIN, sku) -- So com estes dois a serem PK no supplier e que funciona... 
);

------------------------------------------
-- Load data into tables
------------------------------------------

INSERT INTO customer VALUES (1234, 'John', 'john@email.com', 919191919, 'Rua Vasco Paisana n10');
INSERT INTO customer VALUES (1235, 'Mary', 'mary@email.com', 919191555, 'Rua Vasco da Gama n18');
INSERT INTO customer VALUES (1236, 'Paul', 'paul@email.com', 919191444, 'Rua Santa Maria n79');
INSERT INTO customer VALUES (1237, 'Emily', 'emily@email.com', 919191333, 'Avenida 2 de agosto n46');

INSERT INTO order_ VALUES (0000, 1236, '2022-12-09');
INSERT INTO order_ VALUES (1111, 1234, '2023-01-20');
INSERT INTO order_ VALUES (2222, 1235, '2023-01-15');
INSERT INTO order_ VALUES (3333, 1234, '2023-01-26');
INSERT INTO order_ VALUES (4444, 1237, '2023-01-09');

INSERT INTO sale VALUES (1111);
INSERT INTO sale VALUES (4444);

INSERT INTO pay VALUES (1111, 1234);
INSERT INTO pay VALUES (4444, 1237);

INSERT INTO product VALUES ('12345678', 'box', '5cm/7cm/12cm, wooden box', '15.0', 560123456789);
INSERT INTO product VALUES ('12345679', 'pen', 'black ink pen', '37.0', 560123456780);
INSERT INTO product VALUES ('12345670', 'mirror', '170cm/230cm/5cm silver mirror', '58.0', 560123456781);
INSERT INTO product VALUES ('12345671', 'sofa', '2-seat sofa, Vissle beige', '199.0', 560123456782);
INSERT INTO product VALUES ('12345672', 'table', 'table, black, 110x67cm', '50.0', 560123456783);

INSERT INTO contains VALUES (1111, '12345678', 2);
INSERT INTO contains VALUES (1111, '12345670', 1);
INSERT INTO contains VALUES (2222, '12345670', 1);
INSERT INTO contains VALUES (2222, '12345671', 2);
INSERT INTO contains VALUES (2222, '12345672', 1);
INSERT INTO contains VALUES (3333, '12345679', 10);
INSERT INTO contains VALUES (3333, '12345678', 3);
INSERT INTO contains VALUES (0000, '12345670', 3);
INSERT INTO contains VALUES (4444, '12345672', 2);

INSERT INTO employee VALUES (12131415161, '258258258', '1997-04-26', 'Jane Doe');
INSERT INTO employee VALUES (12131415162, '258258321', '1990-07-21', 'Mark Cliff');
INSERT INTO employee VALUES (12131415163, '258258456', '1998-06-26', 'Tom Fizz');
INSERT INTO employee VALUES (12131415164, '258258789', '1995-10-12', 'Catherine Stuart');
INSERT INTO employee VALUES (12131415165, '258258987', '1999-11-04', 'Maggie Green');

INSERT INTO process VALUES (12131415161, 0000);
INSERT INTO process VALUES (12131415162, 1111);
INSERT INTO process VALUES (12131415163, 2222);
INSERT INTO process VALUES (12131415161, 3333);
INSERT INTO process VALUES (12131415164, 4444);

INSERT INTO department VALUES ('Departamento de Gestao de Encomendas');
INSERT INTO department VALUES ('Departamento de Recursos Humanos');

INSERT INTO workplace VALUES ('Estrada da Avessada', 38.927682, -9.257470);
INSERT INTO workplace VALUES ('Avenida da Republica', 38.735465, -9.145027);
INSERT INTO workplace VALUES ('Pacifico', 38.729919, -9.073064);

INSERT INTO works VALUES (12131415161, 'Departamento de Gestao de Encomendas', 'Estrada da Avessada');
INSERT INTO works VALUES (12131415162, 'Departamento de Gestao de Encomendas', 'Estrada da Avessada');
INSERT INTO works VALUES (12131415163, 'Departamento de Gestao de Encomendas', 'Avenida da Republica');
-- INSERT INTO works VALUES (12131415163, 'Departamento de Gestao de Encomendas', 'Pacifico'); (remover para o 2 dar resultado)
INSERT INTO works VALUES (12131415161, 'Departamento de Gestao de Encomendas', 'Pacifico');
INSERT INTO works VALUES (12131415164, 'Departamento de Gestao de Encomendas', 'Avenida da Republica');
INSERT INTO works VALUES (12131415165, 'Departamento de Gestao de Encomendas', 'Estrada da Avessada');

INSERT INTO warehouse VALUES ('Avenida da Republica');
INSERT INTO warehouse VALUES ('Estrada da Avessada');

INSERT INTO office VALUES ('Estrada da Avessada');
INSERT INTO office VALUES ('Pacifico');

INSERT INTO supplier VALUES ('264893401', 'Wooden Space', 'Rua 25 de Fevereiro', '12345678', '2021-09-01');
INSERT INTO supplier VALUES ('268970012', 'BIC', 'Zona Industrial da Venda do Pinheiro', '12345679', '2022-06-01');
INSERT INTO supplier VALUES ('264108994', 'Unividros', 'Ponte do Rol', '12345670', '2023-02-01');
INSERT INTO supplier VALUES ('263329855', 'IKEA', 'Zona Industrial de Alfragide', '12345671', '2016-01-01');
INSERT INTO supplier VALUES ('265977103', 'Movixira Portugal', 'Alverca do Ribatejo', '12345672', '2021-07-01');

INSERT INTO delivery VALUES ('264893401', '12345678', 'Estrada da Avessada');
INSERT INTO delivery VALUES ('268970012', '12345679', 'Estrada da Avessada');
INSERT INTO delivery VALUES ('264108994', '12345670', 'Avenida da Republica');
INSERT INTO delivery VALUES ('263329855', '12345671', 'Avenida da Republica');
INSERT INTO delivery VALUES ('265977103', '12345672', 'Avenida da Republica');