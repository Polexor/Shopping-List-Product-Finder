import re
import pandas as pd

def extract_number_and_unit(text):
    match = re.search(r'(\d+)(\w+)', text)
    if match:
        number, unit = match.groups()
        return f'{number}{unit}'
    return 0


def get_weight(dfr, df_sub):
    weights = []
    final_weights = []

    for idx, item in enumerate(df_sub):
        item_price = dfr.at[idx, 'pricePerItem']
        values = str(item).replace('$', '').split("/")
        unit_price = float(values[0])
        unit_num = (''.join(re.findall(r"\d+", values[1])))
        if unit_num == '':
            unit_num = 1

        units = ''.join(re.findall(r"[a-zA-Z]", values[1]))
        weights.append((item_price, unit_price, unit_num, units))

    for t in weights:
        prod_price = t[0]
        pricePerBasedUnitText_value = t[1]
        pricePerBasedUnitText_weight = t[2]
        if pricePerBasedUnitText_value == 0:
            weight = 0
        else:
            weight = (prod_price / pricePerBasedUnitText_value) * float(pricePerBasedUnitText_weight)
        final_weights.append(f'{round(weight)}{t[3]}')

    return final_weights


if __name__ == '__main__':
    # All data
    df = pd.read_csv('output_all.csv')
    df.fillna('0/0', inplace=True)

    # PAK Cleaned
    df_pak = df[df['storeID'] == 'pak'].reset_index(drop=True)
    pak_price = df_pak['pricePerBaseUnitText']
    df_pak['quantity'] = get_weight(df_pak, pak_price)
    df_pak = df_pak.drop('pricePerBaseUnitText', axis=1)

    # NW Cleaned
    df_new = df[df['storeID'] == 'new'].reset_index(drop=True)
    new_price = df_new['pricePerBaseUnitText']
    df_new['quantity'] = get_weight(df_new, new_price)
    df_new = df_new.drop('pricePerBaseUnitText', axis=1)

    # CD Cleaned
    df_cd = df[df['storeID'] == 'cd'].reset_index(drop=True)
    df_cd['pricePerBaseUnitText'] = df_cd['pricePerBaseUnitText'].apply(extract_number_and_unit)
    df_cd['quantity'] = df_cd['pricePerBaseUnitText']
    df_cd = df_cd.drop('pricePerBaseUnitText', axis=1)

    df_cleaned = pd.concat([df_pak, df_new, df_cd], axis=0).reset_index(drop=True)
    df_cleaned.to_csv('output_cleaned.csv', index=False, mode='w')

    # TODO: Find a new way of comparing prices, Method from pandas/ custom? that takes at least 3 inputs and compares them

    # TODO: Find a way to show the price difference when printing (can do later on)

