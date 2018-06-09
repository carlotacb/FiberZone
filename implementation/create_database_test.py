from rdflib import Namespace, Graph, Literal, RDF

ns = Namespace('ONTOLOGIA_ECSDI/')

def add_product(g, product_id, product_name, product_description, weight_grams, brand, price):
    g.add((ns[product_id], RDF.type, Literal('ONTOLOGIA_ECSDI/product')))
    g.add((ns[product_id], ns.product_name, Literal(product_name)))
    g.add((ns[product_id], ns.product_id, Literal(product_id)))
    g.add((ns[product_id], ns.product_description, Literal(product_description)))
    g.add((ns[product_id], ns.weight_grams, Literal(weight_grams)))
    g.add((ns[product_id], ns.brand, Literal(brand)))
    g.add((ns[product_id], ns.price, Literal(price)))


def add_shop(g, product_id, product_name, product_description, weight_grams, brand, price):
    g.add((ns[product_id], RDF.type, Literal('ONTOLOGIA_ECSDI/shop')))
    g.add((ns[product_id], ns.product_name, Literal(product_name)))
    g.add((ns[product_id], ns.product_id, Literal(product_id)))
    g.add((ns[product_id], ns.product_description, Literal(product_description)))
    g.add((ns[product_id], ns.weight_grams, Literal(weight_grams)))
    g.add((ns[product_id], ns.brand, Literal(brand)))
    g.add((ns[product_id], ns.price, Literal(price)))


def main():
    g = Graph()

    add_product(g, 'B0184OCGAK', 'Kindle 3G', 'Nuevo e-reader Kindle. Lee tus cosas xinas.', 120, 'Amazon', 100)
    add_shop(g, 'B0184OCGAG99', 'Shop Kindle 2G', 'Viejo e-reader Kindle. Lee tus cosas xinas.', 420, 'Amazon', 50)
    add_product(g, 'B0184OCGAG', 'Kindle 2G', 'Viejo e-reader Kindle. Lee tus cosas xinas.', 420, 'Amazon', 50)


    g.serialize('database_test.rdf')
    print('Created product_test.rdf')



main()


